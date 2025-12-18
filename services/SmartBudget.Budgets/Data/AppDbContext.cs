using Microsoft.EntityFrameworkCore;
using SmartBudget.Budgets.Domain.Entities;

namespace SmartBudget.Budgets.Data
{
    public class AppDbContext : DbContext
    {
        public DbSet<Budget> Budget { get; set; } = null!;
        public DbSet<CategoryLimit> CategoryLimits { get; set; } = null!;

        public AppDbContext(DbContextOptions<AppDbContext> options)
            : base(options)
        {
        }

        protected override void OnModelCreating(ModelBuilder mb)
        {
            mb.Entity<Budget>(b =>
            {
                b.ToTable("budgets");
                b.HasKey(x => x.Id);
                b.Property(x => x.UserId).IsRequired();
                b.Property(x => x.Month).IsRequired();
                b.Property(x => x.TotalIncome).HasColumnType("numeric(18,2)");
                b.Property(x => x.Limit).HasColumnType("numeric(18,2)");
                b.Property(x => x.IsAutoRenew).IsRequired();
                b.Property(x => x.CreatedAt).IsRequired();
                b.Property(x => x.UpdatedAt).IsRequired();

                b.HasMany(x => x.CategoryLimits)
                 .WithOne(cl => cl.Budget)
                 .HasForeignKey(cl => cl.BudgetId)
                 .OnDelete(DeleteBehavior.Cascade);
            });

            mb.Entity<CategoryLimit>(b =>
            {
                b.ToTable("category_limits");
                b.HasKey(x => x.Id);
                b.Property(x => x.BudgetId).IsRequired();
                b.Property(x => x.CategoryId).IsRequired();
                b.Property(x => x.Limit).HasColumnType("numeric(18,2)");
                b.Property(x => x.Spent).HasColumnType("numeric(18,2)");
                b.Property(x => x.CreatedAt).IsRequired();
                b.Property(x => x.UpdatedAt).IsRequired();
            });
        }
    }
}