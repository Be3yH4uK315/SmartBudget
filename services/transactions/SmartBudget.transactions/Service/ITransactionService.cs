using SmartBudget.Transactions.DTO;
using System.Text.Json;

namespace SmartBudget.Transactions.Services
{
    public interface ITransactionService
    {
        Task<IEnumerable<object>> GetUserTransactionsAsync(Guid userId, int limit, int offset);
        Task<object?> GetByTransactionIdAsync(Guid transactionId);
        Task<object> CreateManualTransactionAsync(CreateManualTransactionRequest request);
        Task<object> ImportMockAsync(JsonElement body);
        Task<object> PatchCategoryAsync(Guid id, PatchTransactionCategoryRequest request);
        Task DeleteAsync(Guid id);
    }
}
