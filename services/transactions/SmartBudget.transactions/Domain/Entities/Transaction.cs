using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using SmartBudget.Transactions.Domain.Enums;
namespace SmartBudget.Transactions.Domain.Entities
{
/// <summary>
/// Определение сущности Транзакция.
/// </summary>
public class Transaction
{
[Key]
public Guid Id { get; set; }

[Required]
public Guid UserId { get; set; }

public Guid TransactionId { get; set;}

public Guid AccountId { get; set; }

public int? CategoryId { get; set; }

public DateTime? Date { get; set; }

[Column(TypeName = "numeric(18,2)")]
public decimal Value { get; set; }

public TransactionType Type { get; set; }

public TransactionStatus Status { get; set; }

[MaxLength(500)]
public string Merchant { get; set; }

public int? Mcc { get; set; }

[MaxLength(2000)]
public string Description { get; set; }

public DateTime? ImportedAt { get; set; }

public DateTime? UpdatedAt { get; set; }
}
}