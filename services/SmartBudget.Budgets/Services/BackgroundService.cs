using Microsoft.Extensions.Hosting;
using SmartBudget.Budgets.Infrastructure.Kafka;
using SmartBudget.Budgets.Services;

public class BudgetKafkaBackgroundService : BackgroundService
{
    private readonly IKafkaService _kafka;
    private readonly IBudgetService _budgetService;

    public BudgetKafkaBackgroundService(
        IKafkaService kafka,
        IBudgetService budgetService)
    {
        _kafka = kafka;
        _budgetService = budgetService;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await Task.WhenAll(
            _kafka.TransactionNew.ConsumeAsync( _budgetService.NewTransactionAsync, stoppingToken),

            _kafka.TransactionUpdated.ConsumeAsync( _budgetService.UpdatedTransactionAsync, stoppingToken)
        );
    }
}
