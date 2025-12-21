using SmartBudget.Budgets.Domain.Enums;
namespace SmartBudget.Budgets.DTO
{
    public record BudgetEventMessage(string EventType, Guid UserId, object Details);
    public record TransactionNewMessage(Guid UserId, int? CategoryId, decimal Value, TransactionType Type);
    public record TransactionUpdatedMessage(Guid TransactionId, int? OldCategoryId, int? NewCategoryId, decimal Value, TransactionType Type);
}