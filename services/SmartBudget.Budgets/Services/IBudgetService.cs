using SmartBudget.Budgets.Domain.Entities;
using SmartBudget.Budgets.DTO;
using System.Text.Json;

namespace SmartBudget.Budgets.Services
{
    public interface IBudgetService
    {
        Task<Budget?> GetBudgetWithCategoriesAsync(Guid userId, CancellationToken stoppingToken);
        Task<Budget?> GetBudgetSettingsAsync(Guid userId, CancellationToken stoppingToken);
        Task<string> CreateBudgetAsync(Budget budget, CancellationToken stoppingToken);
        Task<Budget?> PatchBudgetAsync(PatchBudgetRequest model, CancellationToken stoppingToken);
        Task NewTransactionAsync(TransactionNewMessage message, CancellationToken stoppingToken);
        Task UpdatedTransactionAsync(TransactionUpdatedMessage message, CancellationToken stoppingToken);


    }

}