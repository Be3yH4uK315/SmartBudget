using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using SmartBudget.Transactions.Domain.DTO;
using SmartBudget.Transactions.Domain.Entities;
using SmartBudget.Transactions.Domain.Enums;
using SmartBudget.Transactions.Infrastructure.Kafka;
using SmartBudget.Transactions.Repositories;

namespace SmartBudget.Transactions.Controllers
{
    [ApiController]
    [Route("api/v1/transactions")]
    public class TransactionsController : ControllerBase
    {
        private readonly ITransactionRepository _repository;
        private readonly IKafkaService _kafka;
        private readonly ILogger<TransactionsController> _log;

        public TransactionsController(ITransactionRepository repository, IKafkaService kafka, ILogger<TransactionsController> log)
        {
            _repository = repository;
            _kafka = kafka;
            _log = log;
        }

        /// <summary>
        /// GET Transactions in list
        /// </summary>
        [HttpGet]
        public async Task<IActionResult> List(
            [FromQuery(Name = "UserId")] Guid userId, 
            [FromQuery(Name = "Limit")] int limit = 50, 
            [FromQuery(Name = "Offset")] int offset = 0)
        {
            var list = await _repository.GetUserTransactionsAsync(userId, limit, offset);

            return Ok(list.Select(new_transaction => new {
                TRANSACTION_ID = new_transaction.TransactionId,
                VALUE = new_transaction.Value,
                CATEGORY_ID = new_transaction.CategoryId,
                DESCRIPTION = new_transaction.Description,
                NAME = new_transaction.Merchant,
                MCC = new_transaction.Mcc,
                STATUS = new_transaction.Status.ToString(),
                DATE = new_transaction.Date?.ToString("o")
            }));
        }


        /// <summary>
        /// GET single transaction
        /// </summary>
        [HttpGet("{id}")]
        public async Task<IActionResult> Get(Guid id)
        {
            var getted_transaction = await _repository.GetByTransactionIdAsync(id);
            if (getted_transaction == null) return NotFound();
            return Ok(getted_transaction);
        }

        /// <summary>
        /// POST create manual transaction
        /// </summary>
        [HttpPost("manual")]
        public async Task<IActionResult> CreateManual([FromBody] CreateManualTransactionRequest _request)
        {
            var created_transaction = new Transaction
            {
                Id = Guid.NewGuid(),
                UserId = _request.userId,
                TransactionId = Guid.NewGuid(),
                AccountId = _request.accountId,
                Value = _request.value,
                Type = _request.value >= 0 ? TransactionType.income : TransactionType.expense,
                Status = TransactionStatus.confirmed,
                Merchant = _request.name,
                Description = _request.description,
                ImportedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow,
                CategoryId = _request.categoryId
            };

            using var transaction = await _repository.BeginTransactionAsync();
            try
            {
                await _repository.AddTransactionAsync(created_transaction);
                await _repository.SaveChangesAsync();

                var simple = JsonSerializer.Serialize(new { ACCOUNT_ID = created_transaction.AccountId, CATEGORY_ID = created_transaction.CategoryId, VALUE = created_transaction.Value });
                await _kafka.ProduceAsync("transaction.new", created_transaction.TransactionId, simple);

                var evt = JsonSerializer.Serialize(new { event_type = "transaction.new", user_id = created_transaction.UserId, details = created_transaction });
                await _kafka.ProduceAsync("budget.transactions.events", created_transaction.TransactionId, evt);

                await transaction.CommitAsync();
            }
            catch
            {
                await transaction.RollbackAsync();
                throw;
            }

            return Ok(new { TRANSACTION_ID = created_transaction.TransactionId });
        }

        /// <summary>
        /// POST import mocks
        /// </summary>
        [HttpPost("import/mock")]
        public async Task<IActionResult> ImportMock([FromBody] JsonElement body)
        {
            List<ImportTransactionItem> items = body.ValueKind switch
            {
                JsonValueKind.Array => JsonSerializer.Deserialize<List<ImportTransactionItem>>(body.GetRawText()),
                JsonValueKind.Object => new List<ImportTransactionItem> { JsonSerializer.Deserialize<ImportTransactionItem>(body.GetRawText()) },
                _ => null
            };

            if (items == null) return BadRequest("Invalid body");

            var created = new List<object>();

            foreach (var current_item in items)
            {
                using var transaction = await _repository.BeginTransactionAsync();
                try
                {
                    var current_imported_transaction = new Transaction
                    {
                        Id = current_item.id == Guid.Empty ? Guid.NewGuid() : current_item.id,
                        UserId = current_item.userId,
                        TransactionId = current_item.transactionId == Guid.Empty ? Guid.NewGuid() : current_item.transactionId,
                        AccountId = current_item.accountId,
                        Date = current_item.date,
                        Value = current_item.value ?? 0,
                        Type = current_item.type ?? TransactionType.expense,
                        Status = current_item.status ?? TransactionStatus.pending,
                        Merchant = current_item.merchant,
                        Mcc = current_item.mcc,
                        Description = current_item.description,
                        ImportedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow,
                        CategoryId = null
                    };

                    if (current_imported_transaction.UserId == Guid.Empty) continue;

                    if (!await _repository.ExistsAsync(current_imported_transaction.TransactionId))
                    {
                        await _repository.AddTransactionAsync(current_imported_transaction);
                        await _repository.SaveChangesAsync();

                        var importedPayload = JsonSerializer.Serialize(new { event_type = "transaction.imported", user_id = current_imported_transaction.UserId, details = current_imported_transaction });
                        await _kafka.ProduceAsync("budget.transactions.events", current_imported_transaction.TransactionId, importedPayload);

                        var need = JsonSerializer.Serialize(new { TRANSACTION_ID = current_imported_transaction.TransactionId, ACCOUNT_ID = current_imported_transaction.AccountId, MERCHANT = current_imported_transaction.Merchant, MCC = current_imported_transaction.Mcc, Description = current_imported_transaction.Description });
                        await _kafka.ProduceAsync("transaction.need_category", current_imported_transaction.TransactionId, need);

                        await transaction.CommitAsync();
                        created.Add(new { current_imported_transaction.TransactionId });
                    }
                }
                catch (Exception exception)
                {
                    await transaction.RollbackAsync();
                    _log.LogError(exception, "Import mock item failed");
                }
            }

            return Ok(new { created_count = created.Count, created });
        }

        /// <summary>
        /// PATCH: change category
        /// </summary>
        [HttpPatch("{id}")]
        public async Task<IActionResult> PatchCategory(Guid id, [FromBody] PatchTransactionCategoryRequest request)
        {
            var tx = await _repository.GetByTransactionIdAsync(id);
            if (tx == null) return NotFound();

            var old = tx.CategoryId;
            tx.CategoryId = request.categoryId;
            tx.UpdatedAt = DateTime.UtcNow;

            await _repository.SaveChangesAsync();

            // Событие для Kafka
            var updated = JsonSerializer.Serialize(new 
            { 
                event_type = "transaction.updated", 
                user_id = tx.UserId, 
                details = new 
                { 
                    TRANSACTION_ID = tx.TransactionId, 
                    OLD_CATEGORY = old, 
                    NEW_CATEGORY = request.categoryId 
                } 
            });
            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, updated);

            var simple = JsonSerializer.Serialize(new 
            { 
                TRANSACTION_ID = tx.TransactionId, 
                OLD_CATEGORY = old, 
                NEW_CATEGORY = request.categoryId 
            });
            await _kafka.ProduceAsync("transaction.updated", tx.TransactionId, simple);

            return Ok("OK");
        }


        /// <summary>
        /// DELETE transaction
        /// </summary>
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(Guid id)
        {
            var deleting_transaction = await _repository.GetByTransactionIdAsync(id);
            if (deleting_transaction == null) return NotFound();

            await _repository.RemoveTransactionAsync(deleting_transaction);
            await _repository.SaveChangesAsync();

            await _kafka.ProduceAsync("budget.transactions.events", deleting_transaction.TransactionId, JsonSerializer.Serialize(new { event_type = "transaction.deleted", user_id = deleting_transaction.UserId, details = new { TRANSACTION_ID = deleting_transaction.TransactionId } }));

            return Ok("OK");
        }
    }
}
