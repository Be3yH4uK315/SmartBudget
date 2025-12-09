using Confluent.Kafka;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Text.Json;


namespace SmartBudget.Transactions.Infrastructure.Kafka
{
public class KafkaService : IKafkaService, IDisposable
{
private readonly IProducer<string, string> _producer;
private readonly ILogger<KafkaService> _log;


public KafkaService(IConfiguration cfg, ILogger<KafkaService> log)
{
_log = log;
var conf = new ProducerConfig
{
BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
Acks = Acks.All
};
_producer = new ProducerBuilder<string, string>(conf).Build();
}

public async Task ProduceAsync(string topic, object payload, string? key = null)
{
    var json = JsonSerializer.Serialize(payload);

    var message = new Message<string, string>
    {
        Key = key ?? Guid.NewGuid().ToString(),
        Value = json
    };

    await _producer.ProduceAsync(topic, message);
}



public void Dispose() => _producer?.Dispose();
}
}