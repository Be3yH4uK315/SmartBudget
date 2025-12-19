using Microsoft.EntityFrameworkCore;
using SmartBudget.Budgets.Data;
using System.Reflection;
using SmartBudget.Budgets.Services;
using System.Net.Mail;
using SmartBudget.Budgets.Infrastructure.Kafka;

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
builder.Services.AddScoped<IBudgetService, BudgetService>();

// Kafka
builder.Services.AddSingleton<IKafkaService, KafkaService>();

//BackgroundService
builder.Services.AddHostedService<BudgetKafkaBackgroundService>();


// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    var xml = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xml);
    c.IncludeXmlComments(xmlPath, includeControllerXmlComments: true);
});

//CORS Policy
builder.Services.AddCors(options =>
{
    options.AddPolicy("FrontendPolicy", policy =>
    {
        policy.WithOrigins("http://127.0.0.1:3000")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();

//CORS
app.UseCors("FrontendPolicy");

// Routing
app.MapControllers();
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.Migrate(); // <-- автоматически применяет все миграции
}

app.Run();