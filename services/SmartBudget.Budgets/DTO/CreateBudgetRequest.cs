using System.Text.Json.Serialization;

namespace SmartBudget.Budgets.DTO
{
    public class CreateBudgetRequest
    {
        [JsonPropertyName("categories")]
        public List<CreateCategoryLimitRequest> Categories { get; set; } = new();

        [JsonPropertyName("totalLimit")]
        public decimal? TotalLimit { get; set; }

        [JsonPropertyName("isAutoRenew")]
        public bool IsAutoRenew { get; set; }
    }

    public class CreateCategoryLimitRequest
    {
        [JsonPropertyName("categoryId")]
        public int CategoryId { get; set; }
        [JsonPropertyName("limit")]
        public decimal Limit { get; set; }
    }

}