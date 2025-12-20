using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SmartBudget.Budgets.Domain.Entities
{
    /// <summary>
    /// Определение сущности Бюджет.
    /// </summary>
    public class Budget
    {
        [Key]
        public Guid Id { get; set; }

        [Required]
        public Guid UserId { get; set; }

        public DateTime Month { get; set; }

        public decimal TotalIncome { get; set; }

        public decimal Limit { get; set; }

        public bool IsAutoRenew { get; set; }

        public DateTime CreatedAt { get; set; }

        public DateTime UpdatedAt { get; set; }
        public ICollection<CategoryLimit> CategoryLimits { get; set; } = new List<CategoryLimit>();
    }
}