namespace SmartBudget.Transactions.DTO
{
    public record TransactionClassifiedMessage(
        Guid TransactionId,
        int? CategoryId
    );
}
