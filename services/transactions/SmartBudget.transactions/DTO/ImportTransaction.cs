using System.Text.Json.Serialization;


namespace SmartBudget.Transactions.Domain.DTO
{
/// <summary>
/// Represents imported transaction item from external source.
/// </summary>
public class ImportTransactionItem
{
[JsonPropertyName("id")]
public string Id { get; set; }


[JsonPropertyName("user_id")]
public string UserId { get; set; }


[JsonPropertyName("transaction_id")]
public string TransactionId { get; set; }


[JsonPropertyName("account_id")]
public string AccountId { get; set; }


[JsonPropertyName("date")]
public string Date { get; set; }


[JsonPropertyName("Value")]
public decimal? Value { get; set; }


[JsonPropertyName("type")]
public string Type { get; set; }


[JsonPropertyName("status")]
public string Status { get; set; }


[JsonPropertyName("merchant")]
public string Merchant { get; set; }


[JsonPropertyName("mcc")]
public int? Mcc { get; set; }


[JsonPropertyName("description")]
public string Description { get; set; }
}
}