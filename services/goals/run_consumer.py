import asyncio
import logging

from app import logging_config, kafka_consumer

if __name__ == "__main__":
    logging_config.setupLogging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Kafka Consumer process...")
    try:
        asyncio.run(kafka_consumer.startConsumer())
    except KeyboardInterrupt:
        logger.info("Consumer process stopped by user.")
    except Exception as e:
        logger.critical(f"Consumer process failed critically: {e}")