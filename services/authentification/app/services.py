import asyncio
from fastapi import Depends
from redis.asyncio import Redis
from uuid import uuid4, UUID
from datetime import datetime, timedelta, timezone
from jwt import encode, decode, PyJWTError
import geoip2.database
from arq.connections import ArqRedis

from app import (
    email_templates, 
    middleware, 
    dependencies,
    redis_keys, 
    schemas, 
    models, 
    utils, 
    settings,
    exceptions,
    repositories
)

class AuthService:
    """Сервис, инкапсулирующий всю бизнес-логику аутентификации."""
    def __init__(
        self,
        UserRepository: repositories.UserRepository = Depends(dependencies.getUserRepository),
        SessionRepository: repositories.SessionRepository = Depends(dependencies.getSessionRepository),
        redis: Redis = Depends(dependencies.getRedis),
        arqPool: ArqRedis = Depends(dependencies.getArqPool),
        geoIpReader: geoip2.database.Reader = Depends(dependencies.getGeoipReader)
    ):
        self.UserRepository = UserRepository
        self.SessionRepository = SessionRepository
        self.redis = redis
        self.arqPool = arqPool
        self.geoIpReader = geoIpReader

    async def startEmailVerification(self, email: str):
        """Проверяет, свободен ли email, и инициирует отправку письма с токеном верификации."""
        existingUser = await self.UserRepository.getByEmail(email)
        if existingUser:
            middleware.logger.warning(f"Verification attempt for existing email: {email}")
            return "sign_in"

        token = str(uuid4())
        hashedToken = utils.hashToken(token)
        redisKey = redis_keys.getVerifyEmailKey(email)
        await self.redis.set(redisKey, hashedToken, ex=900)  # 15 мин TTL

        emailBody = email_templates.getVerificationEmailBody(email, token)

        job = await self.arqPool.enqueue_job(
            'sendEmail',
            to=email,
            subject="Verify your email for SmartBudget",
            body=emailBody,
        )
        middleware.logger.debug(f"Job enqueued: {job.job_id}")

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={"event": "user.verificationStarted", "email": email},
            schemaName="AUTH_EVENTS_SCHEMA"
        )
        return "sign_up"

    async def validateEmailVerificationToken(self, token: str, email: str):
        """Проверяет валидность токена верификации из email."""
        redisKey = redis_keys.getVerifyEmailKey(email)
        eventName = "user.verificationValidated"

        storedHash = await self.redis.get(redisKey)
        if not storedHash or storedHash != utils.hashToken(token):
            middleware.logger.warning(f"Invalid or expired token for verification on email: {email}")
            raise exceptions.InvalidTokenError("Invalid or expired token")

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={"event": eventName, "email": email},
            schemaName="AUTH_EVENTS_SCHEMA"
        )
        middleware.logger.info(f"Token validated for verification on email: {email}, event sent")

    async def validatePasswordResetToken(self, token: str, email: str):
        """Проверяет валидность токена сброса пароля из email."""
        redisKey = redis_keys.getResetPasswordKey(email)
        eventName = "user.passwordResetValidated"

        storedHash = await self.redis.get(redisKey)
        if not storedHash or storedHash != utils.hashToken(token):
            middleware.logger.warning(f"Invalid or expired token for reset on email: {email}")
            raise exceptions.InvalidTokenError("Invalid or expired token")

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={"event": eventName, "email": email},
            schemaName="AUTH_EVENTS_SCHEMA"
        )
        middleware.logger.info(f"Token validated for reset on email: {email}, event sent")

    async def completeRegistration(
        self, 
        body: schemas.CompleteRegistrationRequest,
        ip: str,
        userAgent: str | None
    ):
        """Завершает регистрацию: создает пользователя и сеанс."""
        await self.validateEmailVerificationToken(body.token, body.email)
        redisKey = redis_keys.getVerifyEmailKey(body.email)
        userModel = models.User(
            userId=uuid4(),
            email=body.email,
            name=body.name,
            country=body.country,
            passwordHash=utils.hashPassword(body.password),
            isActive=True,
            role=models.UserRole.USER.value
        )
        user = await self.UserRepository.create(userModel)

        deviceName = utils.parseDevice(userAgent or "Unknown")
        locationData = await asyncio.to_thread(utils.getLocation, ip, self.geoIpReader)
        location = locationData.get("full", "Unknown")

        accessToken, refreshToken, session = await self._createSessionAndTokens(
            user, 
            userAgent or "Unknown",
            deviceName, 
            ip, 
            location
        )

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={
                "event": "user.registered",
                "userId": str(user.userId),
                "email": user.email,
                "ip": ip,
                "location": location
            },
            schemaName="AUTH_EVENTS_SCHEMA"
        )
        await self.redis.delete(redisKey)
        return user, session, accessToken, refreshToken

    async def authenticateUser(
        self, 
        body: schemas.LoginRequest, 
        ip: str,
        userAgent: str | None
    ):
        """Выполняет вход в систему: проверяет учетные данные и создает сеанс."""
        locationData = await asyncio.to_thread(utils.getLocation, ip, self.geoIpReader)
        location = locationData.get("full", "Unknown")

        user = await self.UserRepository.getByEmail(body.email)

        if not user or not user.isActive or not utils.checkPassword(body.password, user.passwordHash):
            await self.arqPool.enqueue_job(
                'sendKafkaEvent',
                topic="auth_events",
                eventData = {
                    "event": "user.loginFailed",
                    "email": body.email,
                    "ip": ip,
                    "location": location,
                },
                schemaName="AUTH_EVENTS_SCHEMA"
            )
            raise exceptions.InvalidCredentialsError("Invalid credentials")

        deviceName = utils.parseDevice(userAgent or "Unknown")

        accessToken, refreshToken, session = await self._createSessionAndTokens(
            user, 
            userAgent or "Unknown",
            deviceName, 
            ip, 
            location
        )

        await self.UserRepository.updateLastLogin(user.userId)

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData = {
                "event": "user.login",
                "userId": str(user.userId),
                "email": user.email,
                "ip": ip,
                "location": location,
            },
            schemaName="AUTH_EVENTS_SCHEMA"
        )
        return user, session, accessToken, refreshToken

    async def logout(self, userId: str, refreshToken: str):
        """Производит выход из системы, отзывая сессию по refresh_token."""
        if not refreshToken:
            raise exceptions.InvalidTokenError("Not authenticated (missing refresh token)")

        fingerprint = utils.hashToken(refreshToken)
        await self.SessionRepository.revokeByFingerprint(UUID(userId), fingerprint)

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={"event": "user.logout", "userId": userId},
            schemaName="AUTH_EVENTS_SCHEMA"
        )

    async def startPasswordReset(self, email: str):
        """Инициирует сброс пароля, если пользователь существует."""
        user = await self.UserRepository.getByEmail(email)
        if not user:
            middleware.logger.warning(f"Password reset attempt for non-existing email: {email}")
            return

        token = str(uuid4())
        hashedToken = utils.hashToken(token)
        redisKey = redis_keys.getResetPasswordKey(email)
        await self.redis.set(redisKey, hashedToken, ex=900)
        
        emailBody = email_templates.getPasswordResetBody(email, token)

        await self.arqPool.enqueue_job(
            'sendEmail',
            to=email,
            subject="Reset your password for SmartBudget",
            body=emailBody,
        )

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={"event": "user.passwordResetStarted", "email": email},
            schemaName="AUTH_EVENTS_SCHEMA"
        )

    async def completePasswordReset(self, body: schemas.CompleteResetRequest):
        """Завершает сброс пароля: проверяет токен и обновляет хэш пароля."""
        await self.validatePasswordResetToken(body.token, body.email)
        redisKey = redis_keys.getResetPasswordKey(body.email)

        user = await self.UserRepository.getByEmail(body.email)
        if not user:
            raise exceptions.UserNotFoundError("User not found")

        await self.UserRepository.updatePassword(user, utils.hashPassword(body.newPassword))
        await self.redis.delete(redisKey)

        await self.SessionRepository.revokeAllForUser(user.userId)

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData = {
                "event": "user.passwordReset",
                "userId": str(user.userId),
                "email": user.email,
            },
            schemaName="AUTH_EVENTS_SCHEMA"
        )

    async def changePassword(self, userId: UUID, body: schemas.ChangePasswordRequest):
        """Изменяет пароль пользователя, используя userId из токена."""
        user = await self.UserRepository.getById(userId)
        if not user or not utils.checkPassword(body.password, user.passwordHash):
            raise exceptions.InvalidCredentialsError("Invalid current password")

        await self.UserRepository.updatePassword(user, utils.hashPassword(body.newPassword))
        await self.SessionRepository.revokeAllForUser(user.userId)

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={"event": "user.passwordChanged", "userId": userId},
            schemaName="AUTH_EVENTS_SCHEMA"
        )

    async def getAllSessions(
        self, 
        userId: UUID, 
        currentRefreshToken: str | None
    ) -> list[schemas.SessionInfo]:
        """Получает все активные сессии для пользователя и помечает, какая является текущей."""
        currentFingerprint = None
        if currentRefreshToken:
            currentFingerprint = utils.hashToken(currentRefreshToken)

        sessions = await self.SessionRepository.getAllActive(userId)

        sessionInfoList = []
        for session in sessions:
            isCurrent = (session.refreshFingerprint == currentFingerprint)
            sessionInfoList.append(
                schemas.SessionInfo(
                    sessionId=session.sessionId,
                    deviceName=session.deviceName,
                    location=session.location,
                    ip=session.ip,
                    createdAt=session.createdAt,
                    isCurrentSession=isCurrent
                )
            )
        return sessionInfoList

    async def revokeSessionById(self, userId: UUID, sessionId: UUID):
        """Отзывает одну конкретную сессию по ID. Проверка userId для безопасности."""
        await self.SessionRepository.revokeById(userId, sessionId)
        middleware.logger.info(f"Session {sessionId} has been revoked by user {userId}")

    async def revokeOtherSessions(self, userId: UUID, currentRefreshToken: str):
        """Отзывает все сессии пользователя, кроме текущей."""
        currentFingerprint = utils.hashToken(currentRefreshToken)
        revokedCount = await self.SessionRepository.revokeAllExcept(userId, currentFingerprint)
        middleware.logger.info(f"Revoked {revokedCount} other sessions for user {userId}")

    async def validateAccessToken(self, token: str):
        """Валидирует access_token."""
        try:
            payload = decode(
                token, 
                settings.settings.JWT.JWT_PUBLIC_KEY,
                algorithms=[settings.settings.JWT.JWT_ALGORITHM],
                issuer="auth-service",
                audience="smart-budget",
            )
            userId = payload.get("sub")
            if not userId:
                raise exceptions.InvalidTokenError("Invalid token (missing sub)")

            user = await self.UserRepository.getById(UUID(userId))
            if not user or not user.isActive:
                raise exceptions.UserInactiveError("User inactive or not found")
        except PyJWTError as e:
            raise exceptions.InvalidTokenError(f"Invalid token: {str(e)}")
        except ValueError:
            raise exceptions.InvalidTokenError("Invalid token payload (bad UUID)")


    async def refreshSession(self, refreshToken: str):
        """Обновляет сеанс с помощью проверки."""
        fingerprint = utils.hashToken(refreshToken)
        session = await self.SessionRepository.getByFingerprint(fingerprint)
        if not session:
            raise exceptions.InvalidTokenError("Invalid refresh token")

        if session.expiresAt < datetime.now(timezone.utc):
            raise exceptions.InvalidTokenError("Refresh token expired")
        
        userId = session.userId
        role = await self.UserRepository.getRoleById(userId)
        
        newAccessToken = self._createAccessToken(str(userId), role)
        newRefreshToken = str(uuid4())
        newFingerprint = utils.hashToken(newRefreshToken)
        await self.SessionRepository.updateFingerprint(
            session, 
            newFingerprint, 
            datetime.now(timezone.utc) + timedelta(days=30)
        )

        await self.arqPool.enqueue_job(
            'sendKafkaEvent',
            topic="auth_events",
            eventData={"event": "user.tokenRefreshed", "userId": str(userId)},
            schemaName="AUTH_EVENTS_SCHEMA"
        )

        return newAccessToken, newRefreshToken

    def _createAccessToken(self, userId: str, role: int) -> str:
        """Генерирует access_token."""
        accessPayload = {
            "sub": userId,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "role": models.UserRole(role).name,
            "iss": "auth-service",
            "aud": "smart-budget"
        }
        return encode(
            accessPayload, 
            settings.settings.JWT.JWT_PRIVATE_KEY,
            algorithm=settings.settings.JWT.JWT_ALGORITHM
        )   
    
    async def _createSessionAndTokens(
        self, 
        user: models.User, 
        userAgent: str | None,
        deviceName: str, 
        ip: str, 
        location: str,
    ):
        """Создает новый сеанс и генерирует токены."""
        refreshToken = str(uuid4())
        fingerprint = utils.hashToken(refreshToken)

        sessionModel = models.Session(
            sessionId=uuid4(),
            userId=user.userId,
            userAgent=userAgent or "Unknown",
            deviceName=deviceName,
            ip=ip,
            location=location,
            revoked=False,
            refreshFingerprint=fingerprint,
            expiresAt=datetime.now(timezone.utc) + timedelta(days=30),
            createdAt=datetime.now(timezone.utc)
        )
        session = await self.SessionRepository.create(sessionModel)
        
        accessToken = self._createAccessToken(str(user.userId), user.role)
        
        return accessToken, refreshToken, session