using System.Text.Json.Serialization;


namespace SmartBudget.Transactions.Domain.DTO
{
/// <summary>
/// Request model for manually created transaction.
/// </summary>
public class CreateManualTransactionRequest
{
public string UserId { get; set; }

public string AccountId { get; set; }

public decimal Value { get; set; }

public int? CategoryId { get; set; }

public string Description { get; set; }

public string Name { get; set; }
}
}