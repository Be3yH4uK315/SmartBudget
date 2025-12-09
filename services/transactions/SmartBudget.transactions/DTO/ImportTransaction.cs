using SmartBudget.Transactions.Domain.Enums;


namespace SmartBudget.Transactions.Domain.DTO
{
/// <summary>
/// Represents imported transaction item from external source.
/// </summary>
public class ImportTransactionItem
{
public Guid id { get; set; }

public Guid userId { get; set; }

public Guid transactionId { get; set; }

public Guid accountId { get; set; }

public DateTime date { get; set; }

public decimal? value { get; set; }

public TransactionType? type { get; set; }

public TransactionStatus? status { get; set; }

public string merchant { get; set; }

public int? mcc { get; set; }

public string description { get; set; }
}
}