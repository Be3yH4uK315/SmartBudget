using System.Text.Json.Serialization;


namespace SmartBudget.Transactions.Domain.DTO
{
/// <summary>
/// Represents imported transaction item from external source.
/// </summary>
public class ImportTransactionItem
{
public string Id { get; set; }

public string UserId { get; set; }

public string TransactionId { get; set; }


public string AccountId { get; set; }

public string Date { get; set; }

public decimal? Value { get; set; }

public string Type { get; set; }

public string Status { get; set; }

public string Merchant { get; set; }

public int? Mcc { get; set; }

public string Description { get; set; }
}
}