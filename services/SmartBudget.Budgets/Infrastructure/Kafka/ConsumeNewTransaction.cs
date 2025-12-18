using Confluent.Kafka;
using System.Text.Json;

namespace SmartBudget.Budgets.Infrastructure.Kafka
{
    public class KafkaTopicConsumer<T> : IKafkaTopicConsumer<T>, IDisposable
    {
        private readonly IConsumer<string, string> _consumer;

        public KafkaTopicConsumer(
            ConsumerConfig config,
            string topic)
        {
            config.EnableAutoCommit = false;
            config.AutoOffsetReset = AutoOffsetReset.Earliest;

            _consumer = new ConsumerBuilder<string, string>(config).Build();
            _consumer.Subscribe(topic);
        }

        public async Task ConsumeAsync(
            Func<T, CancellationToken, Task> handler,
            CancellationToken stoppingToken)
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                ConsumeResult<string, string>? result = null;

                try
                {
                    result = _consumer.Consume(stoppingToken);
                    var message = JsonSerializer.Deserialize<T>(result.Message.Value)!;

                    await handler(message, stoppingToken);

                    _consumer.Commit(result);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch
                {
                    await Task.Delay(1000, stoppingToken);
                }
            }
        }

        public void Dispose()
        {
            _consumer.Close();
            _consumer.Dispose();
        }
    }
}
