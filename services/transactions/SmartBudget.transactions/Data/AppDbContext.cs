using Microsoft.EntityFrameworkCore;
using SmartBudget.Transactions.Domain.Entities;


namespace SmartBudget.Transactions.Data
{

public class AppDbContext : DbContext
{
public DbSet<Transaction> Transactions { get; set; }


public AppDbContext(DbContextOptions<AppDbContext> opts) : base(opts) { }

protected override void OnModelCreating(ModelBuilder mb)
{
mb.Entity<Transaction>(b =>
{
b.ToTable("transactions");
b.HasKey(x => x.Id);
b.Property(x => x.TransactionId).HasMaxLength(200);
b.Property(x => x.Merchant).HasMaxLength(500);
b.Property(x => x.Description).HasMaxLength(2000);
b.Property(x => x.Value).HasColumnType("numeric(18,2)");
});
}
}
}