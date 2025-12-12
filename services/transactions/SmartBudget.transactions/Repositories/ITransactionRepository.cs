using SmartBudget.Transactions.Domain.Entities;
using Microsoft.EntityFrameworkCore.Storage;

namespace SmartBudget.Transactions.Repositories
{
    public interface ITransactionRepository
    {
        Task<List<Transaction>> GetUserTransactionsAsync(Guid userId, int limit, int offset);
        Task<Transaction> GetByTransactionIdAsync(Guid transactionId);
        Task AddTransactionAsync(Transaction transaction);
        Task<bool> ExistsAsync(Guid transactionId);
        Task RemoveTransactionAsync(Transaction transaction);
        Task SaveChangesAsync();
        Task<IDbContextTransaction> BeginTransactionAsync();
    }
}
