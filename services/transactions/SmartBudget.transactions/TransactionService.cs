using Microsoft.EntityFrameworkCore;
using SmartBudget.Transactions.Data;
using SmartBudget.Transactions.Infrastructure.Kafka;
using System.Reflection;
using SmartBudget.Transactions.Services;

var builder = WebApplication.CreateBuilder(args);

// Controllers
builder.Services.AddControllers()
    .AddJsonOptions(o =>
    {
        o.JsonSerializerOptions.PropertyNamingPolicy = null; // keep JSON names from DTO
    });

// DB
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Default")));
//Service
builder.Services.AddScoped<ITransactionService, TransactionService>();
// Kafka
builder.Services.AddSingleton<IKafkaService, KafkaService>();

// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    var xml = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xml);
    c.IncludeXmlComments(xmlPath, includeControllerXmlComments: true);
});

builder.Services.AddCors(options =>
{
    options.AddPolicy("FrontendPolicy", policy =>
    {
        policy.WithOrigins("http://127.0.0.1:3000") // обязательно конкретный адрес
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials(); // ключевое для работы с cookies/auth
    });
});

var app = builder.Build();

app.UseCors("FrontendPolicy");
app.UseSwagger();
app.UseSwaggerUI();

// Routing
app.MapControllers();
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.Migrate(); // <-- автоматически применяет все миграции
}

app.Run();
