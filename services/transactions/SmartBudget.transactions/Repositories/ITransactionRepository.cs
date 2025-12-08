using SmartBudget.Transactions.Domain.Entities;
using Microsoft.EntityFrameworkCore.Storage;

namespace SmartBudget.Transactions.Repositories
{
    public interface ITransactionRepository
    {
        Task<List<Transaction>> GetUserTransactionsAsync(Guid userId, int limit, int offset);
        Task<Transaction> GetByTransactionIdAsync(string transactionId);
        Task AddTransactionAsync(Transaction tx);
        Task<bool> ExistsAsync(string transactionId);
        Task RemoveTransactionAsync(Transaction tx);
        Task SaveChangesAsync();
        Task<IDbContextTransaction> BeginTransactionAsync();
    }
}
