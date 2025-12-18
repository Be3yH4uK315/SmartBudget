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
            try
            {
                while (!stoppingToken.IsCancellationRequested)
                {
                    try
                    {
                        var result = _consumer.Consume(stoppingToken);
                        if (result == null || string.IsNullOrEmpty(result.Message?.Value))
                            continue;

                        var message = JsonSerializer.Deserialize<T>(result.Message.Value);
                        if (message == null) continue;

                        await _handler(message, stoppingToken);

                        _consumer.Commit(result);
                    }
                    catch (ConsumeException ex)
                    {
                        Console.WriteLine($"Kafka consume error: {ex.Error.Reason}");
                        await Task.Delay(1000, stoppingToken); // ждем перед повторной попыткой
                    }
                }
            }
            catch (OperationCanceledException)
            {
                // Graceful shutdown
                Console.WriteLine("Kafka consumer stopping.");
            }
        }

        public void Dispose()
        {
            _consumer.Close();
            _consumer.Dispose();
        }
    }
}
