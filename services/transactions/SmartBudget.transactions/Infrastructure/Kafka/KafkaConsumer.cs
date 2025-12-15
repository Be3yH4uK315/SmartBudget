using Confluent.Kafka;
using System.Text.Json;

namespace SmartBudget.Transactions.Infrastructure.Kafka
{
    public class KafkaTopicConsumer<T> : IKafkaTopicConsumer<T>, IDisposable
    {
        private readonly IConsumer<string, string> _consumer;
        private readonly string _topic;
        private readonly Func<T, CancellationToken, Task> _handler;

        public KafkaTopicConsumer(
            ConsumerConfig config,
            string topic,
            Func<T, CancellationToken, Task> handler)
        {
            _topic = topic;
            _handler = handler;

            _consumer = new ConsumerBuilder<string, string>(config).Build();
            _consumer.Subscribe(topic);
        }

        public async Task ConsumeAsync(CancellationToken stoppingToken)
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                var result = _consumer.Consume(stoppingToken);

                var message = JsonSerializer.Deserialize<T>(result.Message.Value);
                if (message == null) continue;

                await _handler(message, stoppingToken);

                _consumer.Commit(result);
            }
        }

        public void Dispose()
        {
            _consumer.Close();
            _consumer.Dispose();
        }
    }
}
