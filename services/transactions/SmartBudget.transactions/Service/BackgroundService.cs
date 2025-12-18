using Microsoft.Extensions.Hosting;
using SmartBudget.Transactions.DTO;

namespace SmartBudget.Transactions.Infrastructure.Kafka
{
    public class TransactionClassifiedBackgroundService : BackgroundService
    {
        private readonly IKafkaService _kafka;

        public TransactionClassifiedBackgroundService(IKafkaService kafka)
        {
            _kafka = kafka;
        }

        protected override Task ExecuteAsync(CancellationToken stoppingToken)
        {
            return _kafka.TransactionClassified.ConsumeAsync(stoppingToken);
        }
    }
}
