using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using SmartBudget.Budgets.Infrastructure.Kafka;
using SmartBudget.Budgets.Services;

public class BudgetKafkaBackgroundService : BackgroundService
{
    private readonly IKafkaService _kafka;
    private readonly IServiceScopeFactory _scopeFactory;

    public BudgetKafkaBackgroundService(
        IKafkaService kafka,
        IServiceScopeFactory scopeFactory)
    {
        _kafka = kafka;
        _scopeFactory = scopeFactory;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await Task.WhenAll(
            ConsumeNewTransactions(stoppingToken),
            ConsumeUpdatedTransactions(stoppingToken)
        );
    }

    private async Task ConsumeNewTransactions(CancellationToken token)
    {
        await _kafka.TransactionNew.ConsumeAsync(async (msg, ct) =>
        {
            using var scope = _scopeFactory.CreateScope();
            var budgetService = scope.ServiceProvider.GetRequiredService<IBudgetService>();

            await budgetService.NewTransactionAsync(msg, ct);
        }, token);
    }

    private async Task ConsumeUpdatedTransactions(CancellationToken token)
    {
        await _kafka.TransactionUpdated.ConsumeAsync(async (msg, ct) =>
        {
            using var scope = _scopeFactory.CreateScope();
            var budgetService = scope.ServiceProvider.GetRequiredService<IBudgetService>();

            await budgetService.UpdatedTransactionAsync(msg, ct);
        }, token);
    }
}
