namespace SmartBudget.Transactions.DTO
{
    public record TransactionNewMessage(Guid AccountId, int? CategoryId, decimal Value);
    public record BudgetEventMessage(string EventType, Guid UserId, object Details);
    public record TransactionImportedMessage(string EventType, Guid UserId, object Details);
    public record TransactionNeedCategoryMessage(Guid TransactionId, Guid AccountId, string Merchant, int? Mcc, string? Description);
    public record TransactionDeletedMessage(Guid TransactionId, Guid UserId);
    public record TransactionUpdatedMessage(Guid TransactionId, int? OldCategoryId, int? NewCategoryId);
}