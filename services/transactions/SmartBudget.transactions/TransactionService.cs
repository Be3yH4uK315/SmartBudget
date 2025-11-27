// Complete minimal Transaction Service (ASP.NET Core 7)
// Path: services/transactions/TransactionsService.cs
// Single-file sample containing Program, DbContext, Models, Controllers and background services.

using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Confluent.Kafka;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.EntityFrameworkCore.Metadata.Builders;


// -----------------------------
// NOTE
// This is a single-file reference implementation intended to be split into multiple files
// in a real project. It demonstrates the required endpoints, DB model, Kafka produce/consume,
// background tasks for users.active, transaction.classified and periodic bank polling.
// -----------------------------

namespace TransactionsService
{
    public enum TxType { income, expense }
    public enum TxStatus { rejected, confirmed, pending }

    public class Transaction
    {
        [Key]
        public Guid Id { get; set; } // internal UUID primary key

        [Required]
        public Guid UserId { get; set; }

        public string TransactionId { get; set; } // Bank unique ID

        public Guid AccountId { get; set; }

        public Guid? CategoryId { get; set; }

        public DateTime? Date { get; set; }

        [Column(TypeName = "numeric(18,2)")]
        public decimal Amount { get; set; }

        public TxType Type { get; set; }

        public TxStatus Status { get; set; }

        public string Merchant { get; set; }

        public int? Mcc { get; set; }

        public string Description { get; set; }

        public DateTime? ImportedAt { get; set; }

        public DateTime? UpdatedAt { get; set; }
    }

    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> opts) : base(opts) { }
        public DbSet<Transaction> Transactions { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Transaction>(b =>
            {
                b.ToTable("transactions");
                b.HasKey(x => x.Id);
                b.Property(x => x.TransactionId).HasMaxLength(200);
                b.Property(x => x.Merchant).HasMaxLength(500);
                b.Property(x => x.Description).HasMaxLength(2000);
            });
        }
    }

    // DTOs for API
    public class TransactionListItem
    {
        [JsonPropertyName("TRANSACTION_ID")] public string TRANSACTION_ID { get; set; }
        [JsonPropertyName("AMOUNT")] public decimal AMOUNT { get; set; }
        [JsonPropertyName("CATEGORY_ID")] public string CATEGORY_ID { get; set; }
        [JsonPropertyName("DESCRIPTION")] public string DESCRIPTION { get; set; }
        [JsonPropertyName("NAME")] public string NAME { get; set; }
        [JsonPropertyName("MCC")] public int? MCC { get; set; }
        [JsonPropertyName("STATUS")] public string STATUS { get; set; }
        [JsonPropertyName("DATE")] public string DATE { get; set; }
    }

    public class PatchCategoryRequest
    {
        [JsonPropertyName("TRANSACTION_ID")] public string TRANSACTION_ID { get; set; }
        [JsonPropertyName("CATEGORY_ID")] public string CATEGORY_ID { get; set; }
    }

    public class CreateManualTxRequest
    {
        [JsonPropertyName("USER_ID")] public string USER_ID { get; set; }
        [JsonPropertyName("ACCOUNT_ID")] public string ACCOUNT_ID { get; set; }
        [JsonPropertyName("VALUE")] public decimal VALUE { get; set; }
        [JsonPropertyName("CATEGORY_ID")] public string CATEGORY_ID { get; set; }
        [JsonPropertyName("DESCRIPTION")] public string DESCRIPTION { get; set; }
        [JsonPropertyName("NAME")] public string NAME { get; set; }
    }

    // Simple Kafka helper service (producer + simple publish methods)
    public interface IKafkaService
    {
        Task ProduceAsync(string topic, string key, string message);
    }

    public class KafkaService : IKafkaService, IDisposable
    {
        private readonly IProducer<string, string> _producer;
        private readonly ILogger<KafkaService> _logger;

        public KafkaService(IConfiguration cfg, ILogger<KafkaService> logger)
        {
            _logger = logger;
            var conf = new ProducerConfig
            {
                BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
                Acks = Acks.All
            };
            _producer = new ProducerBuilder<string, string>(conf).Build();
        }

        public async Task ProduceAsync(string topic, string key, string message)
        {
            try
            {
                var msg = new Message<string, string> { Key = key, Value = message };
                var res = await _producer.ProduceAsync(topic, msg);
                _logger.LogInformation("Produced to {topic} partition {p} offset {o}", topic, res.Partition, res.Offset);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Kafka produce failed");
            }
        }

        public void Dispose() => _producer?.Dispose();
    }

    // // Background service: consume users.active and trigger bank fetch
    public class UsersActiveConsumer : BackgroundService
    {
        private readonly IConfiguration _cfg;
        private readonly IServiceProvider _sp;
        private readonly ILogger<UsersActiveConsumer> _logger;

        public UsersActiveConsumer(IConfiguration cfg, IServiceProvider sp, ILogger<UsersActiveConsumer> logger)
        {
            _cfg = cfg; _sp = sp; _logger = logger;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            var kafkaServers = _cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092";
            var groupId = _cfg["KAFKA_GROUP_ID"] ?? "transactions-users-active";
            var topic = _cfg["USERS_ACTIVE_TOPIC"] ?? "users.active";

            var conf = new ConsumerConfig
            {
                BootstrapServers = kafkaServers,
                GroupId = groupId,
                AutoOffsetReset = AutoOffsetReset.Earliest
            };

            using var consumer = new ConsumerBuilder<string, string>(conf).Build();
            consumer.Subscribe(topic);
            _logger.LogInformation("UsersActiveConsumer subscribed to {topic}", topic);

            try
            {
                while (!stoppingToken.IsCancellationRequested)
                {
                    try
                    {var cr = consumer.Consume(stoppingToken);
                        if (cr == null) continue;
                        _logger.LogInformation("UsersActiveConsumer got message: {k}", cr.Message?.Key);

                        // Parse payload
                        var doc = JsonDocument.Parse(cr.Message.Value);
                        if (!doc.RootElement.TryGetProperty("user_id", out var userIdEl)) continue;
                        var userId = userIdEl.GetString();

                        // For this user call bank mock API to fetch transactions
                        using var scope = _sp.CreateScope();
                        var http = scope.ServiceProvider.GetRequiredService<HttpClient>();
                        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                        var kafka = scope.ServiceProvider.GetRequiredService<IKafkaService>();

                        var bankUrl = _cfg["BANK_MOCK_URL"] ?? "http://localhost:8080/mock/transactions";
                        var url = $"{bankUrl}?user_id={userId}";
                        _logger.LogInformation("Fetching bank mock for {user}", userId);
                        var resp = await http.GetAsync(url, stoppingToken);
                        if (!resp.IsSuccessStatusCode) continue;
                        var body = await resp.Content.ReadAsStringAsync(stoppingToken);
                        var arr = JsonSerializer.Deserialize<JsonElement[]>(body);
                        foreach (var el in arr)
                        {
                            try
                            {
                                var tx = MapMockToTransaction(el);
                                // insert if not exists
                                var exists = await db.Transactions.AnyAsync(t => t.TransactionId == tx.TransactionId, stoppingToken);
                                if (!exists)
                                {
                                    db.Transactions.Add(tx);
                                    await db.SaveChangesAsync(stoppingToken);

                                    // publish transaction.imported
                                    var importedPayload = JsonSerializer.Serialize(new { event_type = "transaction.imported", user_id = tx.UserId, details = tx });
                                    await kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, importedPayload);

                                    // publish need classification
                                    var need = new {
                                        TRANSACTION_ID = tx.TransactionId,
                                        ACCOUNT_ID = tx.AccountId,
                                        MERCHANT = tx.Merchant,
                                        MCC = tx.Mcc,
                                        Description = tx.Description
                                    };
                                    await kafka.ProduceAsync("transaction.need_category", tx.TransactionId, JsonSerializer.Serialize(need));
                                }
                            }
                            catch (Exception ex)
                            {
                                _logger.LogError(ex, "Failed to process transaction mock element");
                            }
                        }

                    }
                    catch (OperationCanceledException) { break; }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error in UsersActiveConsumer loop");
                        await Task.Delay(1000, stoppingToken);
                    }
                }
            }
            finally
            {
                consumer.Close();
            }
        }

        private Transaction MapMockToTransaction(JsonElement el)
        {
            // Map fields gracefully
            var tx = new Transaction();
            if (el.TryGetProperty("id", out var idEl) && Guid.TryParse(idEl.GetString(), out var id)) tx.Id = id; else tx.Id = Guid.NewGuid();
            if (el.TryGetProperty("user_id", out var uel) && Guid.TryParse(uel.GetString(), out var uid)) tx.UserId = uid;
            if (el.TryGetProperty("transaction_id", out var tel)) tx.TransactionId = tel.GetString();
            if (el.TryGetProperty("account_id", out var ael) && Guid.TryParse(ael.GetString(), out var aid)) tx.AccountId = aid;
            if (el.TryGetProperty("date", out var del) && DateTime.TryParse(del.GetString(), out var d)) tx.Date = d;
            if (el.TryGetProperty("amount", out var mel) && mel.TryGetDecimal(out var amount)) tx.Amount = amount;
            if (el.TryGetProperty("type", out var typ) && Enum.TryParse<TxType>(typ.GetString(), out var tt)) tx.Type = tt;
            if (el.TryGetProperty("status", out var sel) && Enum.TryParse<TxStatus>(sel.GetString(), out var st)) tx.Status = st;
            if (el.TryGetProperty("merchant", out var mer)) tx.Merchant = mer.GetString();
            if (el.TryGetProperty("mcc", out var mcc) && mcc.TryGetInt32(out var mccv)) tx.Mcc = mccv;
            if (el.TryGetProperty("description", out var desc)) tx.Description = desc.GetString();
            if (el.TryGetProperty("imported_at", out var iel) && DateTime.TryParse(iel.GetString(), out var iat)) tx.ImportedAt = iat;
            if (el.TryGetProperty("updated_at", out var uel2) && DateTime.TryParse(uel2.GetString(), out var uat)) tx.UpdatedAt = uat;
            return tx;
        }
    }

    // Background: consume transaction.classified
    public class ClassifiedConsumer : BackgroundService
    {
        private readonly IConfiguration _cfg;
        private readonly IServiceProvider _sp;
        private readonly ILogger<ClassifiedConsumer> _logger;

        public ClassifiedConsumer(IConfiguration cfg, IServiceProvider sp, ILogger<ClassifiedConsumer> logger)
        {
            _cfg = cfg; _sp = sp; _logger = logger;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            var kafkaServers = _cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092";
            var groupId = _cfg["KAFKA_GROUP_ID"] ?? "transactions-classified";
            var topic = _cfg["TRANSACTION_CLASSIFIED_TOPIC"] ?? "transaction.classified";

            var conf = new ConsumerConfig
            {
                BootstrapServers = kafkaServers,
                GroupId = groupId,
                AutoOffsetReset = AutoOffsetReset.Earliest
            };

            using var consumer = new ConsumerBuilder<string, string>(conf).Build();
            consumer.Subscribe(topic);
            _logger.LogInformation("ClassifiedConsumer subscribed to {t}", topic);

            try
            {
                while (!stoppingToken.IsCancellationRequested)
                {
                    try
                    {
                        var cr = consumer.Consume(stoppingToken);
                        if (cr == null) continue;
                        var payload = cr.Message.Value;
                        var doc = JsonDocument.Parse(payload).RootElement;

                        var txId = doc.GetProperty("transaction_id").GetString();
                        var categoryId = doc.GetProperty("category_id").GetString();

                        using var scope = _sp.CreateScope();
                        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                        var kafka = scope.ServiceProvider.GetRequiredService<IKafkaService>();

                        var tx = await db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == txId, stoppingToken);
                        if (tx == null) continue;
                        var oldCategory = tx.CategoryId?.ToString();

                        if (Guid.TryParse(categoryId, out var gid)) tx.CategoryId = gid; else tx.CategoryId = null;
                        tx.UpdatedAt = DateTime.UtcNow;
                        await db.SaveChangesAsync(stoppingToken);

                        // 1) if category == 'Цель' -> publish transaction.goal
                        // NOTE: we can't infer name 'Цель' from UUID; in a real system category metadata is needed.
                        // For demo: assume if categoryId == "goal" (special string) treat as goal.
                        if (categoryId == "Цель" || categoryId == "goal")
                        {
                            var goalMsg = JsonSerializer.Serialize(new {
                                USER_ID = tx.UserId,
                                ACCOUNT_ID = tx.AccountId,
                                AMOUNT = tx.Amount,
                                TYPE = tx.Type.ToString()
                            });
                            await kafka.ProduceAsync("transaction.goal", tx.TransactionId, goalMsg);
                        }

                        // 2) if category == 'Не назначено' -> publish alert to budget.notification
                        if (categoryId == "Не назначено" || categoryId == "unassigned")
                        {
                            var alert = JsonSerializer.Serialize(new { User_id = tx.UserId, transaction_id = tx.TransactionId, merchant = tx.Merchant });
                            await kafka.ProduceAsync("budget.notification", tx.TransactionId, alert);
                        }

                        // 3) publish transaction.new to budget.transactions.events
                        var eventPayload = JsonSerializer.Serialize(new { event_type = "transaction.new", user_id = tx.UserId, details = tx });
                        await kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, eventPayload);

                        // 4) publish transaction.new (simple)
                        var simple = JsonSerializer.Serialize(new { ACCOUNT_ID = tx.AccountId, CATEGORY_ID = tx.CategoryId?.ToString(), AMOUNT = tx.Amount });
                        await kafka.ProduceAsync("transaction.new", tx.TransactionId, simple);

                        // publish transaction.updated as well to budget.transactions.events
                        var upd = JsonSerializer.Serialize(new { event_type = "transaction.updated", user_id = tx.UserId, details = new { TRANSACTION_ID = tx.TransactionId, OLD_CATEGORY = oldCategory, NEW_CATEGORY = categoryId } });
                        await kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, upd);

                    }
                    catch (OperationCanceledException) { break; }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error in ClassifiedConsumer loop");
                        await Task.Delay(1000, stoppingToken);
                    }
                }
            }
            finally { consumer.Close(); }
        }
    }

    //Background: periodic bank poller that iterates users from DB and calls bank webhook
    public class BankPoller : BackgroundService
    {
        private readonly IConfiguration _cfg;
        private readonly IServiceProvider _sp;
        private readonly ILogger<BankPoller> _logger;
        public BankPoller(IConfiguration cfg, IServiceProvider sp, ILogger<BankPoller> logger) { _cfg = cfg; _sp = sp; _logger = logger; }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            var interval = int.TryParse(_cfg["BANK_POLL_INTERVAL"], out var v) ? v : 300; // seconds
            var bankUrl = _cfg["BANK_MOCK_URL"] ?? "http://localhost:8080/mock/transactions";

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    using var scope = _sp.CreateScope();
                    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                    var http = scope.ServiceProvider.GetRequiredService<HttpClient>();
                    var kafka = scope.ServiceProvider.GetRequiredService<IKafkaService>();

                    // For demo: get distinct user ids from transactions table
                    var users = await db.Transactions.Select(t => t.UserId).Distinct().ToListAsync(stoppingToken);
                    foreach (var userId in users)
                    {
                        var url = $"{bankUrl}?user_id={userId}";
                        var resp = await http.GetAsync(url, stoppingToken);
                        if (!resp.IsSuccessStatusCode) continue;
                        var body = await resp.Content.ReadAsStringAsync(stoppingToken);
                        var arr = JsonSerializer.Deserialize<JsonElement[]>(body);
                        foreach (var el in arr)
                        {
                            var tx = MapMockToTransaction(el);
                            var exists = await db.Transactions.AnyAsync(t => t.TransactionId == tx.TransactionId, stoppingToken);
                            if (!exists)
                            {
                                db.Transactions.Add(tx);
                                await db.SaveChangesAsync(stoppingToken);
                                var importedPayload = JsonSerializer.Serialize(new { event_type = "transaction.imported", user_id = tx.UserId, details = tx });
                                await kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, importedPayload);
                                var need = new { TRANSACTION_ID = tx.TransactionId, ACCOUNT_ID = tx.AccountId, MERCHANT = tx.Merchant, MCC = tx.Mcc, Description = tx.Description };
                                await kafka.ProduceAsync("transaction.need_category", tx.TransactionId, JsonSerializer.Serialize(need));
                            }
                        }
                    }

                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "BankPoller error");
                }

                await Task.Delay(TimeSpan.FromSeconds(interval), stoppingToken);
            }
        }

        private Transaction MapMockToTransaction(JsonElement el)
        {
            var tx = new Transaction();
            if (el.TryGetProperty("id", out var idEl) && Guid.TryParse(idEl.GetString(), out var id)) tx.Id = id; else tx.Id = Guid.NewGuid();
            if (el.TryGetProperty("user_id", out var uel) && Guid.TryParse(uel.GetString(), out var uid)) tx.UserId = uid;
            if (el.TryGetProperty("transaction_id", out var tel)) tx.TransactionId = tel.GetString();
            if (el.TryGetProperty("account_id", out var ael) && Guid.TryParse(ael.GetString(), out var aid)) tx.AccountId = aid;
            if (el.TryGetProperty("date", out var del) && DateTime.TryParse(del.GetString(), out var d)) tx.Date = d;
            if (el.TryGetProperty("amount", out var mel) && mel.TryGetDecimal(out var amount)) tx.Amount = amount;
            if (el.TryGetProperty("type", out var typ) && Enum.TryParse<TxType>(typ.GetString(), out var tt)) tx.Type = tt;
            if (el.TryGetProperty("status", out var sel) && Enum.TryParse<TxStatus>(sel.GetString(), out var st)) tx.Status = st;
            if (el.TryGetProperty("merchant", out var mer)) tx.Merchant = mer.GetString();
            if (el.TryGetProperty("mcc", out var mcc) && mcc.TryGetInt32(out var mccv)) tx.Mcc = mccv;
            if (el.TryGetProperty("description", out var desc)) tx.Description = desc.GetString();
            if (el.TryGetProperty("imported_at", out var iel) && DateTime.TryParse(iel.GetString(), out var iat)) tx.ImportedAt = iat;
            if (el.TryGetProperty("updated_at", out var uel2) && DateTime.TryParse(uel2.GetString(), out var uat)) tx.UpdatedAt = uat;
            return tx;
        }
    }

    // API Controllers
    [ApiController]
    [Route("api/v1")]
    public class TransactionsController : ControllerBase
    {
        private readonly AppDbContext _db;
        private readonly IKafkaService _kafka;
        private readonly ILogger<TransactionsController> _logger;

        public TransactionsController(AppDbContext db, IKafkaService kafka, ILogger<TransactionsController> logger)
        {
            _db = db; _kafka = kafka; _logger = logger;
        }

        [HttpGet("transactions")]
        public async Task<IActionResult> List([FromQuery] string USER_ID, [FromQuery] int LIMIT = 50, [FromQuery] int OFFSET = 0)
        {
            if (!Guid.TryParse(USER_ID, out var uid)) return BadRequest("Invalid USER_ID");
            var q = _db.Transactions.Where(t => t.UserId == uid).OrderByDescending(t => t.Date).Skip(OFFSET).Take(LIMIT);
            var list = await q.ToListAsync();
            var res = list.Select(t => ToListItem(t)).ToArray();
            return Ok(res);
        }

        [HttpGet("transactions/{id}")]
        public async Task<IActionResult> Get(string id)
        {
            var tx = await _db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == id);
            if (tx == null) return NotFound();
            return Ok(ToListItem(tx));
        }

        [HttpPatch("transactions/{id}")]
        public async Task<IActionResult> Patch(string id, [FromBody] PatchCategoryRequest req)
        {
            var tx = await _db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == id);
            if (tx == null) return NotFound();
            var oldCat = tx.CategoryId?.ToString();
            if (Guid.TryParse(req.CATEGORY_ID, out var gid)) tx.CategoryId = gid; else tx.CategoryId = null;
            tx.UpdatedAt = DateTime.UtcNow;
            await _db.SaveChangesAsync();

            // publish events
            var kafkaEvent = JsonSerializer.Serialize(new { event_type = "transaction.updated", user_id = tx.UserId, details = new { TRANSACTION_ID = tx.TransactionId, OLD_CATEGORY = oldCat, NEW_CATEGORY = req.CATEGORY_ID } });
            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, kafkaEvent);

            var upd = JsonSerializer.Serialize(new { MERCHANT = tx.Merchant, MCC = tx.Mcc, Description = tx.Description, OLD_CATEGORY = oldCat, NEW_CATEGORY = req.CATEGORY_ID });
            await _kafka.ProduceAsync("transaction.updated", tx.TransactionId, upd);

            return Ok("OK");
        }

        [HttpPost("transactions/manual")]
        public async Task<IActionResult> CreateManual([FromBody] CreateManualTxRequest req)
        {
            if (!Guid.TryParse(req.USER_ID, out var uid)) return BadRequest("USER_ID invalid");
            if (!Guid.TryParse(req.ACCOUNT_ID, out var aid)) return BadRequest("ACCOUNT_ID invalid");
            var tx = new Transaction
            {
                Id = Guid.NewGuid(),
                UserId = uid,
                TransactionId = "MANUAL-" + Guid.NewGuid(),
                AccountId = aid,
                Amount = req.VALUE,
                Type = req.VALUE >= 0 ? TxType.income : TxType.expense,
                Status = TxStatus.confirmed,
                Merchant = req.NAME,
                Description = req.DESCRIPTION,
                ImportedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow,
            };
            if (Guid.TryParse(req.CATEGORY_ID, out var cid)) tx.CategoryId = cid;
            _db.Transactions.Add(tx);
            await _db.SaveChangesAsync();

            // publish events (same as webhook imported but without need_category)
            if (req.CATEGORY_ID == "Цель" || req.CATEGORY_ID == "goal")
            {
                var goalMsg = JsonSerializer.Serialize(new { USER_ID = tx.UserId, ACCOUNT_ID = tx.AccountId, AMOUNT = tx.Amount, TYPE = tx.Type.ToString() });
                await _kafka.ProduceAsync("transaction.goal", tx.TransactionId, goalMsg);
            }
            var simple = JsonSerializer.Serialize(new { ACCOUNT_ID = tx.AccountId, CATEGORY_ID = tx.CategoryId?.ToString(), AMOUNT = tx.Amount });
            await _kafka.ProduceAsync("transaction.new", tx.TransactionId, simple);

            var evt = JsonSerializer.Serialize(new { event_type = "transaction.new", user_id = tx.UserId, details = tx });
            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, evt);

            return Ok(new { TRANSACTION_ID = tx.TransactionId });
        }

        [HttpDelete("transactions/{id}")]
        public async Task<IActionResult> Delete(string id)
        {
            var tx = await _db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == id);
            if (tx == null) return NotFound();
            _db.Transactions.Remove(tx);
            await _db.SaveChangesAsync();

            // publish deletion events
            await _kafka.ProduceAsync("transaction.goal", tx.TransactionId, JsonSerializer.Serialize(new { ACCOUNT_ID = tx.AccountId, AMOUNT = tx.Amount }));
            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, JsonSerializer.Serialize(new { event_type = "transaction.deleted", user_id = tx.UserId, details = new { TRANSACTION_ID = tx.TransactionId } }));

            return Ok("OK");
        }

        [HttpPost("webhook/bank")]
        public async Task<IActionResult> WebhookBank([FromBody] JsonElement body)
        {
            // bank sends single transaction or array
            var kafka = _kafka;
            List<Transaction> received = new List<Transaction>();
            if (body.ValueKind == JsonValueKind.Array)
            {
                foreach (var el in body.EnumerateArray()) received.Add(MapMockToTransaction(el));
            }
            else if (body.ValueKind == JsonValueKind.Object) received.Add(MapMockToTransaction(body));

            foreach (var tx in received)
            {
                var exists = await _db.Transactions.AnyAsync(t => t.TransactionId == tx.TransactionId);
                if (!exists)
                {
                    _db.Transactions.Add(tx);
                    await _db.SaveChangesAsync();

                    var importedPayload = JsonSerializer.Serialize(new { event_type = "transaction.imported", user_id = tx.UserId, details = tx });
                    await kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, importedPayload);

                    var need = new { TRANSACTION_ID = tx.TransactionId, ACCOUNT_ID = tx.AccountId, MERCHANT = tx.Merchant, MCC = tx.Mcc, Description = tx.Description };
                    await kafka.ProduceAsync("transaction.need_category", tx.TransactionId, JsonSerializer.Serialize(need));
                }
            }

            return Ok("OK");
        }

        [HttpGet("health")]
        public IActionResult Health() => Ok(new { status = "ok" });

        private Transaction MapMockToTransaction(JsonElement el)
        {
            var tx = new Transaction();
            if (el.TryGetProperty("id", out var idEl) && Guid.TryParse(idEl.GetString(), out var id)) tx.Id = id; else tx.Id = Guid.NewGuid();
            if (el.TryGetProperty("user_id", out var uel) && Guid.TryParse(uel.GetString(), out var uid)) tx.UserId = uid;
            if (el.TryGetProperty("transaction_id", out var tel)) tx.TransactionId = tel.GetString();
            if (el.TryGetProperty("account_id", out var ael) && Guid.TryParse(ael.GetString(), out var aid)) tx.AccountId = aid;
            if (el.TryGetProperty("date", out var del) && DateTime.TryParse(del.GetString(), out var d)) tx.Date = d;
            if (el.TryGetProperty("amount", out var mel) && mel.TryGetDecimal(out var amount)) tx.Amount = amount;
            if (el.TryGetProperty("type", out var typ) && Enum.TryParse<TxType>(typ.GetString(), out var tt)) tx.Type = tt;
            if (el.TryGetProperty("status", out var sel) && Enum.TryParse<TxStatus>(sel.GetString(), out var st)) tx.Status = st;
            if (el.TryGetProperty("merchant", out var mer)) tx.Merchant = mer.GetString();
            if (el.TryGetProperty("mcc", out var mcc) && mcc.TryGetInt32(out var mccv)) tx.Mcc = mccv;
            if (el.TryGetProperty("description", out var desc)) tx.Description = desc.GetString();
            if (el.TryGetProperty("imported_at", out var iel) && DateTime.TryParse(iel.GetString(), out var iat)) tx.ImportedAt = iat;
            if (el.TryGetProperty("updated_at", out var uel2) && DateTime.TryParse(uel2.GetString(), out var uat)) tx.UpdatedAt = uat;
            return tx;
        }

        private TransactionListItem ToListItem(Transaction t)
        {
            return new TransactionListItem
            {
                TRANSACTION_ID = t.TransactionId,
                AMOUNT = t.Amount,
                CATEGORY_ID = t.CategoryId?.ToString(),
                DESCRIPTION = t.Description,
                NAME = t.Merchant,
                MCC = t.Mcc,
                STATUS = MapStatus(t.Status),
                DATE = t.Date?.ToString("o")
            };
        }

        private string MapStatus(TxStatus s)
        {
            return s switch
            {
                TxStatus.confirmed => "FULFILLED",
                TxStatus.rejected => "REJECTED",
                TxStatus.pending => "PENDING",
                _ => "PENDING"
            };
        }
    }

    // Program entry
    public class Program
    {
        public static void Main(string[] args)
        {
            var builder = WebApplication.CreateBuilder(args);
            var services = builder.Services;
            var config = builder.Configuration;

            services.AddControllers();
            services.AddEndpointsApiExplorer();
            services.AddSwaggerGen();

            // DB
            var pg = config["DATABASE_DSN"] ?? "Host=localhost;Database=smartbudget;Username=postgres;Password=postgres";
            services.AddDbContext<AppDbContext>(opt => opt.UseNpgsql(pg));

            // HttpClient
            services.AddHttpClient();

            // Kafka service
            services.AddSingleton<IKafkaService, KafkaService>();

            // Background consumers
            services.AddHostedService<UsersActiveConsumer>();
            services.AddHostedService<ClassifiedConsumer>();
            services.AddHostedService<BankPoller>();

            var app = builder.Build();
            // apply pending migrations (optional)
            using var scope = app.Services.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            var retries = 10;
            while (retries > 0)
            {
                try
                {
                    db.Database.Migrate();
                    break;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Database not ready yet: {ex.Message}");
                    retries--;
                    if (retries == 0) throw;
                    Thread.Sleep(2000);
                }
            }


            if (app.Environment.IsDevelopment())
            {
                app.UseSwagger();
                app.UseSwaggerUI();
            }

            app.MapControllers();
            app.Run();
        }
    }
}



