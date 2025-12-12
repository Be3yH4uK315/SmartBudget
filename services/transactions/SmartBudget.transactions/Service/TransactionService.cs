using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using SmartBudget.Transactions.Data;
using SmartBudget.Transactions.DTO;
using SmartBudget.Transactions.Domain.Entities;
using SmartBudget.Transactions.Domain.Enums;
using SmartBudget.Transactions.Infrastructure.Kafka;

namespace SmartBudget.Transactions.Services
{
    public class TransactionService : ITransactionService
    {
        private readonly AppDbContext _db;
        private readonly IKafkaService _kafka;
        private readonly ILogger<TransactionService> _log;

        public TransactionService(AppDbContext db, IKafkaService kafka, ILogger<TransactionService> log)
        {
            _db = db;
            _kafka = kafka;
            _log = log;
        }

        public async Task<IEnumerable<object>> GetUserTransactionsAsync(Guid UserId, int Limit, int Offset)
        {
            var list = await _db.Transactions
                .Where(new_transaction => new_transaction.UserId == UserId)
                .OrderByDescending(new_transaction => new_transaction.CreatedAt)
                .Skip(Offset)
                .Take(Limit)
                .ToListAsync();

            return list.Select(new_transaction => new {
                transactionId = new_transaction.TransactionId,
                value = new_transaction.Value,
                categoryId = new_transaction.CategoryId,
                description = new_transaction.Description,
                name = new_transaction.Merchant,
                mcc = new_transaction.Mcc,
                status = new_transaction.Status.ToString(),
                date = new_transaction.CreatedAt.ToString("o"),
                type = new_transaction.Type.ToString()
            });
        }

        public async Task<object?> GetByTransactionIdAsync(Guid transactionId)
        {
            return await _db.Transactions.FirstOrDefaultAsync(new_transaction => new_transaction.TransactionId == transactionId);
        }

        public async Task<object> CreateManualTransactionAsync(CreateManualTransactionRequest request)
        {
            var transaction = new Transaction
            {
                Id = Guid.NewGuid(),
                UserId = request.UserId,
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

            using var transactionBD = await _db.Database.BeginTransactionAsync();
            try
            {
                _db.Transactions.Add(transaction);
                await _db.SaveChangesAsync();

                await _kafka.TransactionNew.ProduceAsync( transaction.TransactionId, new TransactionNewMessage( transaction.AccountId, transaction.CategoryId, transaction.Value ));

                await _kafka.BudgetEvents.ProduceAsync(transaction.TransactionId, new BudgetEventMessage( "transaction.new", transaction.UserId, transaction ));

                await transactionBD.CommitAsync();
            }
            catch
            {
                await transactionBD.RollbackAsync();
                throw;
            }

            return new { transactionId = transaction.TransactionId };
        }


        public async Task<object> ImportMockAsync(JsonElement body)
        {
            List<ImportTransactionItem> items = body.ValueKind switch
            {
                JsonValueKind.Array => JsonSerializer.Deserialize<List<ImportTransactionItem>>(body.GetRawText()),
                JsonValueKind.Object => new List<ImportTransactionItem> { JsonSerializer.Deserialize<ImportTransactionItem>(body.GetRawText()) },
                _ => null
            };

            if (items == null) throw new Exception("Invalid body");

            var created = new List<object>();

            foreach (var current_transaction in items)
            {
                using var transactionBD = await _db.Database.BeginTransactionAsync();
                try
                {
                    var new_transaction = new Transaction
                    {
                        Id = current_transaction.Id == Guid.Empty ? Guid.NewGuid() : current_transaction.Id,
                        UserId = current_transaction.UserId,
                        TransactionId = current_transaction.TransactionId == Guid.Empty ? Guid.NewGuid() : current_transaction.TransactionId,
                        AccountId = current_transaction.AccountId,
                        Date = current_transaction.Date,
                        Value = current_transaction.Value ?? 0,
                        Type = current_transaction.Type ?? TransactionType.expense,
                        Status = current_transaction.Status ?? TransactionStatus.pending,
                        Merchant = current_transaction.Merchant,
                        Mcc = current_transaction.Mcc,
                        Description = current_transaction.Description,
                        CreatedAt = current_transaction.Date,
                        ImportedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow,
                        CategoryId = null
                    };

                    if (new_transaction.UserId == Guid.Empty) continue;

                    if (!await _db.Transactions.AnyAsync(x => x.TransactionId == new_transaction.TransactionId))
                    {
                        _db.Transactions.Add(new_transaction);
                        await _db.SaveChangesAsync();

                        await _kafka.TransactionImported.ProduceAsync(new_transaction.TransactionId, new TransactionImportedMessage("transaction.imported", new_transaction.UserId, new_transaction ) );

                        await _kafka.TransactionNeedCategory.ProduceAsync( new_transaction.TransactionId, new TransactionNeedCategoryMessage( new_transaction.TransactionId, new_transaction.AccountId, new_transaction.Merchant, new_transaction.Mcc, new_transaction.Description ) );

                        await transactionBD.CommitAsync();
                        created.Add(new { new_transaction.TransactionId });
                    }
                }
                catch (Exception except)
                {
                    await transactionBD.RollbackAsync();
                    _log.LogError(except, "Import mock failed");
                }
            }

            return new { created_count = created.Count, created };
        }

        public async Task<object> PatchCategoryAsync(Guid Id, PatchTransactionCategoryRequest request)
        {
            var transaction = await _db.Transactions.FirstOrDefaultAsync(new_transaction => new_transaction.TransactionId == Id);
            if (transaction == null) throw new Exception("Not found");

            var old = transaction.CategoryId;
            transaction.CategoryId = request.CategoryId;
            transaction.UpdatedAt = DateTime.UtcNow;

            await _db.SaveChangesAsync();

            await _kafka.TransactionUpdated.ProduceAsync( transaction.TransactionId, new TransactionUpdatedMessage( transaction.TransactionId, old, request.CategoryId ) );

            await _kafka.BudgetEvents.ProduceAsync( transaction.TransactionId, new BudgetEventMessage( "transaction.updated", transaction.UserId, new { transaction.TransactionId, OldCategoryId = old, NewCategoryId = request.CategoryId } ) );

            return "OK";
        }

        public async Task DeleteAsync(Guid Id)
        {
            var transaction = await _db.Transactions.FirstOrDefaultAsync(new_transaction => new_transaction.TransactionId == Id);
            if (transaction == null) return;

            _db.Transactions.Remove(transaction);
            await _db.SaveChangesAsync();

            await _kafka.TransactionDeleted.ProduceAsync( transaction.TransactionId, new TransactionDeletedMessage( transaction.TransactionId, transaction.UserId ) );

            await _kafka.BudgetEvents.ProduceAsync( transaction.TransactionId,   new BudgetEventMessage(    "transaction.deleted",  transaction.UserId,   new { transaction.TransactionId }  ) );
        }
    }
}
