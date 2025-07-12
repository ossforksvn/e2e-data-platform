from pyspark.sql import SparkSession
from pyspark import SparkConf

conf = SparkConf() \
    .set("spark.driver.cores", "1") \
    .set("spark.driver.memory", "512m") \
    .set("spark.executor.cores", "1") \
    .set("spark.executor.memory", "512m")

spark = SparkSession.builder \
    .appName("Just say hi") \
    .config(conf=conf) \
    .enableHiveSupport() \
    .getOrCreate()

print("Just say hi")

