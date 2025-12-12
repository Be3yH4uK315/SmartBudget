namespace SmartBudget.Transactions.Infrastructure.Kafka
{
/// <summary>
/// Абстракция на сообщение в кафку.
/// </summary>
public interface IKafkaService
{
    Task ProduceAsync(string topic, object payload, string? key = null);
}
}