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
        private readonly ITransactionRepository _repo;
        private readonly IKafkaService _kafka;
        private readonly ILogger<TransactionsController> _log;

        public TransactionsController(ITransactionRepository repo, IKafkaService kafka, ILogger<TransactionsController> log)
        {
            _repo = repo;
            _kafka = kafka;
            _log = log;
        }

        /// <summary>
        /// GET Transactions in list
        /// </summary>
        [HttpGet]
        public async Task<IActionResult> List([FromQuery] string USER_ID, [FromQuery] int LIMIT = 50, [FromQuery] int OFFSET = 0)
        {
            if (!Guid.TryParse(USER_ID, out var uid)) return BadRequest("Invalid USER_ID");

            var list = await _repo.GetUserTransactionsAsync(uid, LIMIT, OFFSET);

            return Ok(list.Select(t => new {
                TRANSACTION_ID = t.TransactionId,
                VALUE = t.Value,
                CATEGORY_ID = t.CategoryId,
                DESCRIPTION = t.Description,
                NAME = t.Merchant,
                MCC = t.Mcc,
                STATUS = t.Status.ToString(),
                DATE = t.Date?.ToString("o")
            }));
        }

        /// <summary>
        /// GET single transaction
        /// </summary>
        [HttpGet("{id}")]
        public async Task<IActionResult> Get(string id)
        {
            var tx = await _repo.GetByTransactionIdAsync(id);
            if (tx == null) return NotFound();
            return Ok(tx);
        }

        /// <summary>
        /// POST create manual transaction
        /// </summary>
        [HttpPost("manual")]
        public async Task<IActionResult> CreateManual([FromBody] CreateManualTransactionRequest req)
        {
            if (!Guid.TryParse(req.UserId, out var uid)) return BadRequest("USER_ID invalid");
            if (!Guid.TryParse(req.AccountId, out var aid)) return BadRequest("ACCOUNT_ID invalid");

            var tx = new Transaction
            {
                Id = Guid.NewGuid(),
                UserId = uid,
                TransactionId = "MANUAL-" + Guid.NewGuid(),
                AccountId = aid,
                Value = req.Value,
                Type = req.Value >= 0 ? TransactionType.income : TransactionType.expense,
                Status = TransactionStatus.confirmed,
                Merchant = req.Name,
                Description = req.Description,
                ImportedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow,
                CategoryId = req.CategoryId
            };

            using var transaction = await _repo.BeginTransactionAsync();
            try
            {
                await _repo.AddTransactionAsync(tx);
                await _repo.SaveChangesAsync();

                var simple = JsonSerializer.Serialize(new { ACCOUNT_ID = tx.AccountId, CATEGORY_ID = tx.CategoryId, VALUE = tx.Value });
                await _kafka.ProduceAsync("transaction.new", tx.TransactionId, simple);

                var evt = JsonSerializer.Serialize(new { event_type = "transaction.new", user_id = tx.UserId, details = tx });
                await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, evt);

                await transaction.CommitAsync();
            }
            catch
            {
                await transaction.RollbackAsync();
                throw;
            }

            return Ok(new { TRANSACTION_ID = tx.TransactionId });
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

            foreach (var it in items)
            {
                using var transaction = await _repo.BeginTransactionAsync();
                try
                {
                    var tx = new Transaction
                    {
                        Id = Guid.TryParse(it.Id, out var gid) ? gid : Guid.NewGuid(),
                        UserId = Guid.TryParse(it.UserId, out var uid) ? uid : Guid.Empty,
                        TransactionId = it.TransactionId ?? Guid.NewGuid().ToString(),
                        AccountId = Guid.TryParse(it.AccountId, out var aid) ? aid : Guid.Empty,
                        Date = DateTime.TryParse(it.Date, out var d) ? d : (DateTime?)null,
                        Value = it.Value ?? 0m,
                        Type = Enum.TryParse<TransactionType>(it.Type ?? "expense", true, out var tt) ? tt : TransactionType.expense,
                        Status = Enum.TryParse<TransactionStatus>(it.Status ?? "pending", true, out var st) ? st : TransactionStatus.pending,
                        Merchant = it.Merchant,
                        Mcc = it.Mcc,
                        Description = it.Description,
                        ImportedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow,
                        CategoryId = null
                    };

                    if (tx.UserId == Guid.Empty) continue;

                    if (!await _repo.ExistsAsync(tx.TransactionId))
                    {
                        await _repo.AddTransactionAsync(tx);
                        await _repo.SaveChangesAsync();

                        var importedPayload = JsonSerializer.Serialize(new { event_type = "transaction.imported", user_id = tx.UserId, details = tx });
                        await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, importedPayload);

                        var need = JsonSerializer.Serialize(new { TRANSACTION_ID = tx.TransactionId, ACCOUNT_ID = tx.AccountId, MERCHANT = tx.Merchant, MCC = tx.Mcc, Description = tx.Description });
                        await _kafka.ProduceAsync("transaction.need_category", tx.TransactionId, need);

                        await transaction.CommitAsync();
                        created.Add(new { tx.TransactionId });
                    }
                }
                catch (Exception ex)
                {
                    await transaction.RollbackAsync();
                    _log.LogError(ex, "Import mock item failed");
                }
            }

            return Ok(new { created_count = created.Count, created });
        }

        /// <summary>
        /// PATCH: change category
        /// </summary>
        [HttpPatch("{id}")]
        public async Task<IActionResult> PatchCategory(string id, [FromBody] PatchTransactionCategoryRequest req)
        {
            var tx = await _repo.GetByTransactionIdAsync(id);
            if (tx == null) return NotFound();

            var old = tx.CategoryId;
            tx.CategoryId = req.CategoryId;
            tx.UpdatedAt = DateTime.UtcNow;

            await _repo.SaveChangesAsync();

            // Событие для Kafka
            var upd = JsonSerializer.Serialize(new 
            { 
                event_type = "transaction.updated", 
                user_id = tx.UserId, 
                details = new 
                { 
                    TRANSACTION_ID = tx.TransactionId, 
                    OLD_CATEGORY = old, 
                    NEW_CATEGORY = req.CategoryId 
                } 
            });
            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, upd);

            var simple = JsonSerializer.Serialize(new 
            { 
                TRANSACTION_ID = tx.TransactionId, 
                OLD_CATEGORY = old, 
                NEW_CATEGORY = req.CategoryId 
            });
            await _kafka.ProduceAsync("transaction.updated", tx.TransactionId, simple);

            return Ok("OK");
        }


        /// <summary>
        /// DELETE transaction
        /// </summary>
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(string id)
        {
            var tx = await _repo.GetByTransactionIdAsync(id);
            if (tx == null) return NotFound();

            await _repo.RemoveTransactionAsync(tx);
            await _repo.SaveChangesAsync();

            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, JsonSerializer.Serialize(new { event_type = "transaction.deleted", user_id = tx.UserId, details = new { TRANSACTION_ID = tx.TransactionId } }));

            return Ok("OK");
        }
    }
}
