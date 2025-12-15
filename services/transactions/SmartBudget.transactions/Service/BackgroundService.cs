using Microsoft.Extensions.Hosting;
using SmartBudget.Transactions.DTO;

namespace SmartBudget.Transactions.Infrastructure.Kafka
{
    public class TransactionClassifiedBackgroundService : BackgroundService
    {
        private readonly IKafkaTopicConsumer<TransactionClassifiedMessage> _consumer;

        public TransactionClassifiedBackgroundService(
            IKafkaTopicConsumer<TransactionClassifiedMessage> consumer)
        {
            _consumer = consumer;
        }

        protected override Task ExecuteAsync(CancellationToken stoppingToken)
        {
            return _consumer.ConsumeAsync(stoppingToken);
        }
    }
}
