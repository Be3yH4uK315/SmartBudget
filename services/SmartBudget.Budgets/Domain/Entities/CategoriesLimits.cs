using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SmartBudget.Budgets.Domain.Entities
{
    /// <summary>
    /// Определение сущности Бюджет.
    /// </summary>
    public class CategoryLimit
    {
        [Key]
        public Guid Id { get; set; }

        [Required]
        public Guid BudgetId { get; set; }

        [ForeignKey(nameof(BudgetId))]
        public Budget Budget { get; set; } = null!;

        public int CategoryId { get; set; }

        public decimal Limit { get; set; }

        public decimal Spent { get; set; }

        public DateTime? CreatedAt { get; set; }

        public DateTime? UpdatedAt { get; set; }
    }
}