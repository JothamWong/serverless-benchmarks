--
-- Licensed to the Apache Software Foundation (ASF) under one or more
-- contributor license agreements.  See the NOTICE file distributed with
-- this work for additional information regarding copyright ownership.
-- The ASF licenses this file to You under the Apache License, Version 2.0
-- (the "License"); you may not use this file except in compliance with
-- the License.  You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{\"object\":{\"model\": \"resnet50-19c8e357.pth\", \"input\": \"800px-Porsche_991_silver_IAA.jpg\"}, \"bucket\": {\"bucket\": \"sebs-benchmarks-9594b98e\", \"input\": \"411.image-recognition-1-input\", \"model\": \"411.image-recognition-0-input\"}}"
