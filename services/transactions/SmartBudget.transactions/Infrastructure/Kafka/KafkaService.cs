using Confluent.Kafka;
using System.Text.Json;
using SmartBudget.Transactions.DTO;
using SmartBudget.Transactions.Services;


namespace SmartBudget.Transactions.Infrastructure.Kafka
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
        public IKafkaTopicConsumer<TransactionClassifiedMessage> TransactionClassified { get; }
        public IKafkaTopicProducer<TransactionNewMessage> TransactionNew { get; }
        public IKafkaTopicProducer<TransactionNewGoalMessage> TransactionNewGoal { get; }
        public IKafkaTopicProducer<TransactionImportedMessage> TransactionImported { get; }
        public IKafkaTopicProducer<TransactionNeedCategoryMessage> TransactionNeedCategory { get; }
        public IKafkaTopicProducer<TransactionUpdatedMessage> TransactionUpdated { get; }
        public IKafkaTopicProducer<TransactionDeletedMessage> TransactionDeleted { get; }

        public IKafkaTopicProducer<BudgetEventMessage> BudgetEvents { get; }

        private readonly List<IDisposable> _producers = new();
        public KafkaService(IConfiguration cfg, ClassificationHandler handler)
        {
            var config = new ProducerConfig
            {
                BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
                Acks = Acks.All
            };
            var consumerConfig = new ConsumerConfig
            {
                BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
                GroupId = "transactions-service",
                AutoOffsetReset = AutoOffsetReset.Earliest,
                EnableAutoCommit = false
            };

            TransactionNew = Add(new KafkaTopicProducer<TransactionNewMessage>(config, "transaction.new"));
            TransactionImported = Add(new KafkaTopicProducer<TransactionImportedMessage>(config, "transaction.imported"));
            TransactionNewGoal = Add(new KafkaTopicProducer<TransactionNewGoalMessage>(config, "transaction.goal"));
            TransactionNeedCategory = Add(new KafkaTopicProducer<TransactionNeedCategoryMessage>(config, "transaction.need_category"));
            TransactionUpdated = Add(new KafkaTopicProducer<TransactionUpdatedMessage>(config, "transaction.updated"));
            TransactionDeleted = new KafkaTopicProducer<TransactionDeletedMessage>(config, "transaction.deleted");
            BudgetEvents = Add(new KafkaTopicProducer<BudgetEventMessage>(config, "budget.transactions.events"));
            TransactionClassified = Add(new KafkaTopicConsumer<TransactionClassifiedMessage>(
            consumerConfig,
            "transaction.classified",
            handler.HandleAsync
        ));
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