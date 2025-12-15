using SmartBudget.Transactions.Domain.Enums;


namespace SmartBudget.Transactions.DTO
{
    /// <summary>
    /// Represents imported transaction item from external source.
    /// </summary>
    public class ImportTransactionItem
    {
        public Guid Id { get; set; }

        public Guid UserId { get; set; }

        public Guid TransactionId { get; set; }

        public Guid AccountId { get; set; }

        public DateTime Date { get; set; }

        public decimal? Value { get; set; }

        public TransactionType? Type { get; set; }

        public TransactionStatus? Status { get; set; }

        public string Merchant { get; set; }

        public int? Mcc { get; set; }

        public string Description { get; set; }
    }
}