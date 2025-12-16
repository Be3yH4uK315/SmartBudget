using SmartBudget.Transactions.DTO;
using SmartBudget.Transactions.Domain.Entities;
using System.Text.Json;

namespace SmartBudget.Transactions.Services
{
    public interface ITransactionService
{
    Task<List<Transaction>> GetUserTransactionsAsync(Guid userId, int limit, int offset, int category_id, CancellationToken stoppingToken);
    Task<Transaction?> GetByTransactionIdAsync(Guid transactionId, CancellationToken stoppingToken);
    Task<string> CreateManualTransactionAsync(Transaction transaction, CancellationToken stoppingToken);
    Task<int> ImportMockAsync(List<Transaction> transactions, CancellationToken stoppingToken);
    Task<string> PatchCategoryAsync(Guid id, PatchTransactionCategoryRequest request, CancellationToken stoppingToken);
    Task DeleteAsync(Guid id, CancellationToken stoppingToken);
}

}
