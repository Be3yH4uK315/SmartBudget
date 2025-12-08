using System.Text.Json.Serialization;


namespace SmartBudget.Transactions.Domain.DTO
{
/// <summary>
/// Request model for manually created transaction.
/// </summary>
public class CreateManualTransactionRequest
{
[JsonPropertyName("USER_ID")]
public string UserId { get; set; }


[JsonPropertyName("ACCOUNT_ID")]
public string AccountId { get; set; }


[JsonPropertyName("VALUE")]
public decimal Value { get; set; }


[JsonPropertyName("CATEGORY_ID")]
public int? CategoryId { get; set; }


[JsonPropertyName("DESCRIPTION")]
public string Description { get; set; }


[JsonPropertyName("NAME")]
public string Name { get; set; }
}
}