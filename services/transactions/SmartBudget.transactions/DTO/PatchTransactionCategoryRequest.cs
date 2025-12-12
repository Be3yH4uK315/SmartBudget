using System.Text.Json.Serialization;
namespace SmartBudget.Transactions.DTO
{
    /// <summary>
    /// Модель запроса для изменения категории транзакции
    /// </summary>
    public class PatchTransactionCategoryRequest
    {
        [JsonPropertyName("categoryId")]
        public int? CategoryId { get; set; }
    }
}
