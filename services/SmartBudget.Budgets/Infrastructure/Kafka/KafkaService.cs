using Confluent.Kafka;
using System.Text.Json;
using SmartBudget.Budgets.DTO;
using SmartBudget.Budgets.Services;


namespace SmartBudget.Budgets.Infrastructure.Kafka
{
    public class KafkaTopicProducer<T> : IKafkaTopicProducer<T>, IDisposable
    {
        private readonly IProducer<string, string> _producer;
        private readonly string _topic;

        public KafkaTopicProducer(ProducerConfig config, string topic)
        {
            _topic = topic;
            _producer = new ProducerBuilder<string, string>(config).Build();
        }

        public async Task ProduceAsync(string key, T message, CancellationToken stoppingToken)
        {
            var json = JsonSerializer.Serialize(message);

            await _producer.ProduceAsync(
                _topic,
                new Message<string, string>
                {
                    Key = key,
                    Value = json
                },
                stoppingToken
            );
        }



        public void Dispose() => _producer?.Dispose();
    }

    public class KafkaService : IKafkaService, IDisposable
    {
        public IKafkaTopicProducer<BudgetEventMessage> BudgetEvents { get; }
        public IKafkaTopicConsumer<TransactionNewMessage> TransactionNew { get; }
        public IKafkaTopicConsumer<TransactionUpdatedMessage> TransactionUpdated { get; }

        private readonly List<IDisposable> _producers = new();
        public KafkaService(IConfiguration cfg)
        {
            var config = new ProducerConfig
            {
                BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
                Acks = Acks.All
            };
            var consumerConfig = new ConsumerConfig
            {
                BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
                GroupId = "budgets-service",
                AutoOffsetReset = AutoOffsetReset.Earliest,
                EnableAutoCommit = false
            };

            BudgetEvents = Add(new KafkaTopicProducer<BudgetEventMessage>(config, "budget.budgets.events"));
            TransactionNew = Add(new KafkaTopicConsumer<TransactionNewMessage>(consumerConfig, "transaction.new"));
            TransactionUpdated = Add(new KafkaTopicConsumer<TransactionUpdatedMessage>(consumerConfig, "transaction.updated"));

        }
        private T Add<T>(T producer) where T : IDisposable
        {
            _producers.Add(producer);
            return producer;
        }

        public void Dispose()
        {
            foreach (var p in _producers) p.Dispose();
        }
    }

}
