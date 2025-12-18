using Microsoft.EntityFrameworkCore;
using SmartBudget.Transactions.Data;
using SmartBudget.Transactions.DTO;

namespace SmartBudget.Transactions.Services
{
    public class ClassificationHandler
    {
        private readonly AppDbContext _db;
        private readonly ILogger<ClassificationHandler> _log;

        public ClassificationHandler(
            AppDbContext db,
            ILogger<ClassificationHandler> log)
        {
            _db = db;
            _log = log;
        }

        public async Task HandleAsync(
            TransactionClassifiedMessage message,
            CancellationToken ct)
        {
            using var transactionBD = await _db.Database.BeginTransactionAsync();
            try
            {
                var transaction = await _db.Transactions
                .FirstOrDefaultAsync(
                    x => x.TransactionId == message.TransactionId,
                    ct);

                if (transaction == null)
                {
                    _log.LogWarning(
                        "Transaction {TransactionId} not found for classification",
                        message.TransactionId);
                    return;
                }

                transaction.CategoryId = message.CategoryId;
                transaction.UpdatedAt = DateTime.UtcNow;

                await _db.SaveChangesAsync(ct);
                await transactionBD.CommitAsync();
            }
            catch (Exception except)
            {
                await transactionBD.RollbackAsync();
                _log.LogError(except, "Setting category failed");
            }
        }
    }
}
