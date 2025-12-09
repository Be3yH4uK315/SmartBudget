namespace SmartBudget.Transactions.Domain.DTO
{
    /// <summary>
    /// Модель запроса для изменения категории транзакции
    /// </summary>
    public class PatchTransactionCategoryRequest
    {
        public int? categoryId { get; set; }
    }
}
