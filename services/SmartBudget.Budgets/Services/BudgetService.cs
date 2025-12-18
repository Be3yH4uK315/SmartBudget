using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using SmartBudget.Budgets.Data;
using SmartBudget.Budgets.Domain.Entities;
using SmartBudget.Budgets.Services;
using SmartBudget.Budgets.Infrastructure.Kafka;
using SmartBudget.Budgets.DTO;
using SmartBudget.Budgets.Domain.Enums;
using Microsoft.AspNetCore.Http.HttpResults;

namespace SmartBudget.Budgets.Services
{
    public class BudgetService : IBudgetService
    {
        private readonly AppDbContext _db;
        private readonly IKafkaService _kafka;
        private readonly ILogger<BudgetService> _log;

        public BudgetService(AppDbContext db, IKafkaService kafka, ILogger<BudgetService> log)
        {
            _db = db;
            _kafka = kafka;
            _log = log;
        }

        public async Task<Budget?> GetBudgetWithCategoriesAsync(Guid userId, CancellationToken stoppingToken)
        {
            return await _db.Budget
                .Include(b => b.CategoryLimits)
                .FirstOrDefaultAsync(b => b.UserId == userId, stoppingToken);
        }
        public async Task<Budget?> GetBudgetSettingsAsync(Guid userId, CancellationToken stoppingToken)
        {
            return await _db.Budget
                .Include(b => b.CategoryLimits.Where(cl => cl.Limit != 0))
                .FirstOrDefaultAsync(b => b.UserId == userId, stoppingToken);
        }

        public async Task<string> CreateBudgetAsync(Budget budget, CancellationToken stoppingToken)
        {
            await using var transaction = await _db.Database.BeginTransactionAsync(stoppingToken);
            try
            {
                _db.Budget.Add(budget);
                await _db.SaveChangesAsync(stoppingToken);

                await _kafka.BudgetEvents.ProduceAsync(budget.Id.ToString(), new BudgetEventMessage("budget.created", budget.Id, budget.Limit), stoppingToken);

                await transaction.CommitAsync(stoppingToken);

            }
            catch (Exception except)
            {
                await transaction.RollbackAsync(stoppingToken);
                _log.LogError(except, "Creating budget failed");
            }
            return budget.Id.ToString();
        }
        public async Task<Budget?> PatchBudgetAsync(PatchBudgetRequest model, CancellationToken stoppingToken)
        {
            var budget = await _db.Budget
                .Include(b => b.CategoryLimits)
                .FirstOrDefaultAsync(b => b.UserId == model.UserId, stoppingToken);

            if (budget == null)
                return null;
            await using var transaction = await _db.Database.BeginTransactionAsync(stoppingToken);
            try
            {
                var now = DateTime.UtcNow;

                if (model.TotalLimit.HasValue)
                    budget.Limit = model.TotalLimit.Value;

                if (model.IsAutoRenew.HasValue)
                    budget.IsAutoRenew = model.IsAutoRenew.Value;

                budget.UpdatedAt = now;

                foreach (var incoming in model.Categories)
                {
                    var existing = budget.CategoryLimits
                        .FirstOrDefault(c => c.CategoryId == incoming.CategoryId);

                    if (existing != null)
                    {
                        existing.Limit = incoming.Limit;
                        existing.UpdatedAt = now;
                    }
                    else
                    {
                        budget.CategoryLimits.Add(new CategoryLimit
                        {
                            Id = Guid.NewGuid(),
                            BudgetId = budget.Id,
                            CategoryId = incoming.CategoryId,
                            Limit = incoming.Limit,
                            Spent = 0,
                            CreatedAt = now,
                            UpdatedAt = now
                        });
                    }
                }
                await _db.SaveChangesAsync(stoppingToken);
            }
            catch (Exception except)
            {
                await transaction.RollbackAsync(stoppingToken);
                _log.LogError(except, "Patch settings failed");
            }
            return budget;

        }
        public async Task NewTransactionAsync(
    TransactionNewMessage message,
    CancellationToken stoppingToken)
        {
            await using var tx = await _db.Database.BeginTransactionAsync(stoppingToken);

            try
            {
                var budget = await _db.Budget
                    .Include(b => b.CategoryLimits)
                    .FirstOrDefaultAsync(
                        b => b.UserId == message.AccountId,
                        stoppingToken);

                if (budget == null)
                {
                    _log.LogWarning("Budget not found for account {AccountId}", message.AccountId);
                    return;
                }

                if (!message.CategoryId.HasValue)
                    return; // транзакция без категории — игнорируем

                var category = budget.CategoryLimits
                    .FirstOrDefault(c => c.CategoryId == message.CategoryId.Value);

                if (category == null)
                {
                    category = new CategoryLimit
                    {
                        Id = Guid.NewGuid(),
                        BudgetId = budget.Id,
                        CategoryId = message.CategoryId.Value,
                        Limit = 0,
                        Spent = 0,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    };

                    budget.CategoryLimits.Add(category);
                }
                category.Spent += message.Type == TransactionType.expense ? message.Value : -message.Value;
                category.UpdatedAt = DateTime.UtcNow;
                budget.UpdatedAt = DateTime.UtcNow;

                await _db.SaveChangesAsync(stoppingToken);
                await tx.CommitAsync(stoppingToken);
            }
            catch (Exception ex)
            {
                await tx.RollbackAsync(stoppingToken);
                _log.LogError(ex, "Failed to apply new transaction");
                throw;
            }
        }
        public async Task UpdatedTransactionAsync(TransactionUpdatedMessage message, CancellationToken stoppingToken)
        {
            await using var tx = await _db.Database.BeginTransactionAsync(stoppingToken);

            try
            {
                var budget = await _db.Budget
                    .Include(b => b.CategoryLimits)
                    .FirstOrDefaultAsync(
                        b => b.UserId == message.TransactionId, // тут уточни: нужен ли AccountId?
                        stoppingToken);

                if (budget == null)
                {
                    _log.LogWarning("Budget not found for transaction {TransactionId}", message.TransactionId);
                    return;
                }

                // Уменьшаем старую категорию
                if (message.OldCategoryId.HasValue)
                {
                    var oldCategory = budget.CategoryLimits
                        .FirstOrDefault(c => c.CategoryId == message.OldCategoryId.Value);

                    if (oldCategory == null)
                    {
                        oldCategory = new CategoryLimit
                        {
                            Id = Guid.NewGuid(),
                            BudgetId = budget.Id,
                            CategoryId = message.OldCategoryId.Value,
                            Limit = 0,
                            Spent = 0,
                            CreatedAt = DateTime.UtcNow,
                            UpdatedAt = DateTime.UtcNow
                        };
                        budget.CategoryLimits.Add(oldCategory);
                    }

                    oldCategory.Spent -= message.Type == TransactionType.expense ? message.Value : -message.Value;
                    oldCategory.UpdatedAt = DateTime.UtcNow;
                }

                if (message.NewCategoryId.HasValue)
                {
                    var newCategory = budget.CategoryLimits
                        .FirstOrDefault(c => c.CategoryId == message.NewCategoryId.Value);

                    if (newCategory == null)
                    {
                        newCategory = new CategoryLimit
                        {
                            Id = Guid.NewGuid(),
                            BudgetId = budget.Id,
                            CategoryId = message.NewCategoryId.Value,
                            Limit = 0,
                            Spent = 0,
                            CreatedAt = DateTime.UtcNow,
                            UpdatedAt = DateTime.UtcNow
                        };
                        budget.CategoryLimits.Add(newCategory);
                    }

                    newCategory.Spent += message.Type == TransactionType.expense ? message.Value : -message.Value;
                    newCategory.UpdatedAt = DateTime.UtcNow;
                }

                budget.UpdatedAt = DateTime.UtcNow;

                await _db.SaveChangesAsync(stoppingToken);
                await tx.CommitAsync(stoppingToken);
            }
            catch (Exception ex)
            {
                await tx.RollbackAsync(stoppingToken);
                _log.LogError(ex, "Failed to update transaction");
                throw;
            }
        }
    }
}
