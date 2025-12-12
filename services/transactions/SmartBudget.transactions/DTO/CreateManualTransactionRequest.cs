using System.Text.Json.Serialization;

namespace SmartBudget.Transactions.Domain.DTO

{
/// <summary>
/// Request model for manually created transaction.
/// </summary>
public class CreateManualTransactionRequest
{
[JsonPropertyName("userId")]
public Guid UserId { get; set; }

[JsonPropertyName("accountId")]
public Guid AccountId { get; set; }

[JsonPropertyName("value")]
public decimal Value { get; set; }

[JsonPropertyName("categoryId")]
public int? CategoryId { get; set; }

[JsonPropertyName("desctiption")]
public string Description { get; set; }

[JsonPropertyName("name")]
public string Name { get; set; }
}
}