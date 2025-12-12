namespace SmartBudget.Transactions.Domain.DTO
{
/// <summary>
/// Request model for manually created transaction.
/// </summary>
public class CreateManualTransactionRequest
{
public Guid userId { get; set; }

public Guid accountId { get; set; }

public decimal value { get; set; }

public int? categoryId { get; set; }

public string description { get; set; }

public string name { get; set; }
}
}