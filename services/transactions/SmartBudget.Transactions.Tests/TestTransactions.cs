using System;
using System.Net;
using System.Net.Http.Json;
using System.Threading.Tasks;
using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using TransactionsService;
using Xunit;
using System.Linq;
using System.Net.Http;

namespace TransactionsService.Tests
{
    // Mock Kafka для проверки сообщений
    public class MockKafkaService : IKafkaService
    {
        public readonly System.Collections.Generic.List<(string Topic, string Key, string Message)> ProducedMessages
            = new();

        public Task ProduceAsync(string topic, string key, string message)
        {
            ProducedMessages.Add((topic, key, message));
            return Task.CompletedTask;
        }
    }

    // Фабрика тестового приложения для реального сервиса
    public class TestApplicationFactory : WebApplicationFactory<Program>
    {
        protected override void ConfigureWebHost(Microsoft.AspNetCore.Hosting.IWebHostBuilder builder)
        {
            builder.ConfigureServices(services =>
            {
                // Подменяем KafkaService на Mock, чтобы не подключаться к реальному Kafka
                var kafkaDescriptor = services.SingleOrDefault(d => d.ServiceType == typeof(IKafkaService));
                if (kafkaDescriptor != null) services.Remove(kafkaDescriptor);
                services.AddSingleton<IKafkaService, MockKafkaService>();

                // Можно отключить фоновые сервисы, чтобы не пытались подключаться к Kafka
                var bgServices = services.Where(s => s.ImplementationType != null &&
                                                     typeof(Microsoft.Extensions.Hosting.IHostedService)
                                                     .IsAssignableFrom(s.ImplementationType))
                                         .ToList();
                foreach (var s in bgServices)
                    services.Remove(s);
            });
        }
    }

    public class TransactionsControllerTests : IClassFixture<TestApplicationFactory>
    {
        private readonly HttpClient _client;
        private readonly MockKafkaService _mockKafka;

        public TransactionsControllerTests(TestApplicationFactory factory)
        {
            _client = factory.CreateClient(); // реальные HTTP-запросы к запущенному сервису
            var scope = factory.Services.CreateScope();
            _mockKafka = scope.ServiceProvider.GetRequiredService<IKafkaService>() as MockKafkaService;
        }

        [Fact]
        public async Task Health_ReturnsOk()
        {
            var resp = await _client.GetAsync("/api/v1/health");
            resp.StatusCode.Should().Be(HttpStatusCode.OK);
        }

        [Fact]
        public async Task CreateManual_Get_Patch_Delete_Workflow()
        {
            // 1. Создаём manual транзакцию
            var createReq = new CreateManualTxRequest
            {
                USER_ID = Guid.NewGuid().ToString(),
                ACCOUNT_ID = Guid.NewGuid().ToString(),
                VALUE = 123.45m,
                NAME = "Test Merchant",
                DESCRIPTION = "Test Description",
                CATEGORY_ID = null
            };

            var createResp = await _client.PostAsJsonAsync("/api/v1/transactions/manual", createReq);
            createResp.StatusCode.Should().Be(HttpStatusCode.OK);
            var created = await createResp.Content.ReadFromJsonAsync<CreateManualTxResponse>();
            created.Should().NotBeNull();
            created.TRANSACTION_ID.Should().NotBeNullOrEmpty();

            var txId = created.TRANSACTION_ID;

            // 2. Получаем транзакцию по id
            var getResp = await _client.GetAsync($"/api/v1/transactions/{txId}");
            getResp.StatusCode.Should().Be(HttpStatusCode.OK);

            // 3. Патчим категорию
            var patchReq = new PatchCategoryRequest
            {
                TRANSACTION_ID = txId,
                CATEGORY_ID = Guid.NewGuid().ToString()
            };
            var patchResp = await _client.PatchAsJsonAsync($"/api/v1/transactions/{txId}", patchReq);
            patchResp.StatusCode.Should().Be(HttpStatusCode.OK);

            // 4. Удаляем транзакцию
            var delResp = await _client.DeleteAsync($"/api/v1/transactions/{txId}");
            delResp.StatusCode.Should().Be(HttpStatusCode.OK);

            // 5. Проверяем, что Kafka получил события через Mock
            _mockKafka.ProducedMessages.Should().NotBeEmpty();
        }

        private class CreateManualTxResponse
        {
            public string TRANSACTION_ID { get; set; }
        }
    }
}
