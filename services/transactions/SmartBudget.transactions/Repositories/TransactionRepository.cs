using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using SmartBudget.Transactions.Data;
using SmartBudget.Transactions.Domain.Entities;


namespace SmartBudget.Transactions.Repositories
{
    public class TransactionRepository : ITransactionRepository
    {
        private readonly AppDbContext _db;
        public TransactionRepository(AppDbContext db) => _db = db;

        public Task<List<Transaction>> GetUserTransactionsAsync(Guid userId, int limit, int offset)
            => _db.Transactions
                .Where(t => t.UserId == userId)
                .OrderByDescending(t => t.Date)
                .Skip(offset).Take(limit)
                .ToListAsync();

        public Task<Transaction> GetByTransactionIdAsync(string transactionId)
            => _db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == transactionId);

        public Task AddTransactionAsync(Transaction tx)
        {
            _db.Transactions.Add(tx);
            return Task.CompletedTask;
        }

        public Task<bool> ExistsAsync(string transactionId)
            => _db.Transactions.AnyAsync(t => t.TransactionId == transactionId);

        public Task RemoveTransactionAsync(Transaction tx)
        {
            _db.Transactions.Remove(tx);
            return Task.CompletedTask;
        }

        public Task SaveChangesAsync() => _db.SaveChangesAsync();

        public Task<IDbContextTransaction> BeginTransactionAsync() => _db.Database.BeginTransactionAsync();
    }
}
