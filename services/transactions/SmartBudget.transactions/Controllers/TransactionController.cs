using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using SmartBudget.Transactions.DTO;
using SmartBudget.Transactions.Domain.Entities;
using SmartBudget.Transactions.Domain.Enums;
using SmartBudget.Transactions.Infrastructure.Kafka;
using SmartBudget.Transactions.Services;
using System.Text.Json.Serialization;

using Microsoft.EntityFrameworkCore.Diagnostics;

namespace SmartBudget.Transactions.Controllers
{
    [ApiController]
    [Route("api/v1/transactions")]
    public class TransactionsController : ControllerBase
    {
        private readonly ITransactionService _service;

        public TransactionsController(ITransactionService service)
        {
            _service = service;
        }

        /// <summary>
        /// GET Transactions in list
        /// </summary>
        [HttpGet]
        public async Task<IActionResult> List(
            [FromHeader(Name = "X-User-Id")] Guid userId,
            [FromQuery(Name = "limit")] int limit = 50,
            [FromQuery(Name = "offset")] int offset = 0,
            [FromQuery(Name = "categoryId")] int category_id = 0,
            CancellationToken stoppingToken = default)
        {
            List<Transaction> list =
                await _service.GetUserTransactionsAsync(userId, limit, offset, category_id, stoppingToken);

            return Ok(list.Select(new_transaction => new
            {
                transactionId = new_transaction.TransactionId,
                value = new_transaction.Value,
                categoryId = new_transaction.CategoryId,
                description = new_transaction.Description,
                name = new_transaction.Merchant,
                mcc = new_transaction.Mcc,
                status = new_transaction.Status.ToString(),
                date = new_transaction.CreatedAt.ToString("o"),
                type = new_transaction.Type.ToString()
            }));
        }

        /// <summary>
        /// GET single transaction
        /// </summary>
        [HttpGet("{id}")]
        public async Task<IActionResult> Get(Guid id, CancellationToken stoppingToken = default)
        {
            var result = await _service.GetByTransactionIdAsync(id, stoppingToken);
            return result == null ? NotFound() : Ok(result);
        }

        /// <summary>
        /// POST create manual transaction
        /// </summary>
        [HttpPost("manual")]
        public async Task<IActionResult> CreateManual(
            [FromHeader(Name = "X-User-Id")] Guid userId,
            [FromBody] CreateManualTransactionRequest request,
            CancellationToken stoppingToken = default)
        {
            Transaction transaction = new Transaction
            {
                Id = Guid.NewGuid(),
                UserId = userId,
                TransactionId = Guid.NewGuid(),
                AccountId = request.AccountId,
                Value = request.Value,
                Type = request.Value >= 0 ? TransactionType.income : TransactionType.expense,
                Status = TransactionStatus.confirmed,
                Merchant = request.Name,
                Description = request.Description,
                CreatedAt = DateTime.UtcNow,
                ImportedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow,
                CategoryId = request.CategoryId
            };

            return Ok(await _service.CreateManualTransactionAsync(transaction, stoppingToken));
        }

        /// <summary>
        /// POST import mocks
        /// </summary>
        [HttpPost("import/mock")]
        public async Task<IActionResult> ImportMock(
    [FromBody] JsonElement body,
    CancellationToken stoppingToken = default)
        {
            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            // JsonStringEnumConverter поддерживает nullable enum с StringCaseInsensitive
            options.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.CamelCase, allowIntegerValues: false));

            List<ImportTransactionItem> items = body.ValueKind switch
            {
                JsonValueKind.Array => JsonSerializer.Deserialize<List<ImportTransactionItem>>(body.GetRawText(), options),
                JsonValueKind.Object => new List<ImportTransactionItem>
        {
            JsonSerializer.Deserialize<ImportTransactionItem>(body.GetRawText(), options)
        },
                _ => null
            };

            if (items == null)
                throw new Exception("Invalid body");

            var imported = new List<Transaction>();

            foreach (var current_transaction in items)
            {
                if (current_transaction.UserId == Guid.Empty)
                    continue;
                var transactionDateUtc = DateTime.SpecifyKind(current_transaction.Date, DateTimeKind.Utc);
                var imported_transaction = new Transaction
                {
                    Id = current_transaction.Id == Guid.Empty ? Guid.NewGuid() : current_transaction.Id,
                    UserId = current_transaction.UserId,
                    TransactionId = current_transaction.TransactionId == Guid.Empty
                        ? Guid.NewGuid()
                        : current_transaction.TransactionId,
                    AccountId = current_transaction.AccountId,
                    Value = current_transaction.Value ?? 0,
                    Type = current_transaction.Type ?? TransactionType.expense,
                    Status = current_transaction.Status ?? TransactionStatus.pending,
                    Merchant = current_transaction.Merchant,
                    Mcc = current_transaction.Mcc,
                    Description = current_transaction.Description,
                    CreatedAt = transactionDateUtc,
                    ImportedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow,
                    CategoryId = current_transaction.CategoryId,
                };

                imported.Add(imported_transaction);
            }

            return Ok(await _service.ImportMockAsync(imported, stoppingToken));
        }

        /// <summary>
        /// PATCH: change category
        /// </summary>
        [HttpPatch("edit/{id}")]
        public async Task<IActionResult> PatchCategory(
            Guid id,
            [FromBody] PatchTransactionCategoryRequest request,
            CancellationToken stoppingToken = default)
        {
            return Ok(await _service.PatchCategoryAsync(id, request, stoppingToken));
        }

        /// <summary>
        /// DELETE transaction
        /// </summary>
        [HttpDelete("edit/{id}")]
        public async Task<IActionResult> Delete(Guid id, CancellationToken stoppingToken = default)
        {
            await _service.DeleteAsync(id, stoppingToken);
            return Ok();
        }

        /// <summary>
        /// GET transactions for goals
        /// </summary>
        [HttpGet("goals/{accountId}")]
        public async Task<IActionResult> Goals( Guid accountId,CancellationToken stoppingToken = default)
        {
            return Ok(await _service.GetUserTransactionsGoalsAsync(accountId, stoppingToken));
        }
        /// <summary>
        /// Health check endpoint
        /// </summary>
        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new { status = "Healthy" });
        }


    }
}
