using SmartBudget.Transactions.Domain.Enums;

namespace SmartBudget.Transactions.DTO
{

    public class TransactionsByMonth
    {
        public decimal Value { get; set; }
        public DateTime Date { get; set; }
        public TransactionType Type { get; set; }
    }
}
