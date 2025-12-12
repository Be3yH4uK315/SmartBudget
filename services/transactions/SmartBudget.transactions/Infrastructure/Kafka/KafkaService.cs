using Confluent.Kafka;
using System.Text.Json;
using SmartBudget.Transactions.DTO;


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

    public async Task ProduceAsync(object key, T message)
    {
        var json = JsonSerializer.Serialize(message);

        await _producer.ProduceAsync(_topic, new Message<string, string>
        {
            Key = key.ToString(),
            Value = json
        });
    }

    public void Dispose() => _producer?.Dispose();
}

public class KafkaService : IKafkaService, IDisposable
{
    public IKafkaTopicProducer<TransactionNewMessage> TransactionNew { get; }
    public IKafkaTopicProducer<TransactionImportedMessage> TransactionImported { get; }
    public IKafkaTopicProducer<TransactionNeedCategoryMessage> TransactionNeedCategory { get; }
    public IKafkaTopicProducer<TransactionUpdatedMessage> TransactionUpdated { get; }
    public IKafkaTopicProducer<TransactionDeletedMessage> TransactionDeleted { get; }

    public IKafkaTopicProducer<BudgetEventMessage> BudgetEvents { get; }

    private readonly List<IDisposable> _producers = new();

    public KafkaService(IConfiguration cfg)
    {
        var config = new ProducerConfig
        {
            BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
            Acks = Acks.All
        };

        TransactionNew = Add(new KafkaTopicProducer<TransactionNewMessage>(config, "transaction.new"));
        TransactionImported = Add(new KafkaTopicProducer<TransactionImportedMessage>(config, "transaction.imported"));
        TransactionNeedCategory = Add(new KafkaTopicProducer<TransactionNeedCategoryMessage>(config, "transaction.need_category"));
        TransactionUpdated = Add(new KafkaTopicProducer<TransactionUpdatedMessage>(config, "transaction.updated"));
        TransactionDeleted = new KafkaTopicProducer<TransactionDeletedMessage>(config, "transaction.deleted");
        BudgetEvents = Add(new KafkaTopicProducer<BudgetEventMessage>(config, "budget.transactions.events"));
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