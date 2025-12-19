using System.Text.Json.Serialization;

namespace SmartBudget.Budgets.DTO
{
    public class PatchBudgetRequest
    {
        [JsonPropertyName("totalLimit")]
        public decimal? TotalLimit { get; init; }

        [JsonPropertyName("isAutoRenew")]
        public bool? IsAutoRenew { get; init; }

        [JsonPropertyName("categories")]
        public List<PatchCategoryLimitRequest> Categories { get; init; } = new();
    }

    public class PatchCategoryLimitRequest
    {
        [JsonPropertyName("categoryId")]
        public int CategoryId { get; init; }
        
        [JsonPropertyName("limit")]
        public decimal Limit { get; init; }
    }
}