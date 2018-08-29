provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "outputs" {
  bucket = "jh-dn-dcgan-hubble"
  acl    = "private"
}

resource "aws_vpc" "main" {
  cidr_block                       = "10.0.0.0/16"
  assign_generated_ipv6_cidr_block = true
}

resource "aws_subnet" "public_us-east-1a" {
  vpc_id                          = "${aws_vpc.main.id}"
  availability_zone               = "us-east-1a"
  cidr_block                      = "10.0.1.0/24"
  ipv6_cidr_block                 = "${cidrsubnet(aws_vpc.main.ipv6_cidr_block, 8, 1)}"
  map_public_ip_on_launch         = true
  assign_ipv6_address_on_creation = true
}

resource "aws_subnet" "public_us-east-1b" {
  vpc_id                          = "${aws_vpc.main.id}"
  availability_zone               = "us-east-1b"
  cidr_block                      = "10.0.2.0/24"
  ipv6_cidr_block                 = "${cidrsubnet(aws_vpc.main.ipv6_cidr_block, 8, 2)}"
  map_public_ip_on_launch         = true
  assign_ipv6_address_on_creation = true
}

resource "aws_subnet" "public_us-east-1e" {
  vpc_id                          = "${aws_vpc.main.id}"
  availability_zone               = "us-east-1e"
  cidr_block                      = "10.0.3.0/24"
  ipv6_cidr_block                 = "${cidrsubnet(aws_vpc.main.ipv6_cidr_block, 8, 3)}"
  map_public_ip_on_launch         = true
  assign_ipv6_address_on_creation = true
}

resource "aws_security_group" "main" {
  name        = "main"
  description = "Allow any outbound connections, allow SSH inbound"

  vpc_id = "${aws_vpc.main.id}"

  ingress {
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    ipv6_cidr_blocks = ["::/0"]
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = -1
    ipv6_cidr_blocks = ["::/0"]
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = "${aws_vpc.main.id}"
}

resource "aws_route_table" "main" {
  vpc_id = "${aws_vpc.main.id}"
}

resource "aws_route" "public_default_v4" {
  route_table_id              = "${aws_route_table.main.id}"
  destination_ipv6_cidr_block = "::/0"
  gateway_id                  = "${aws_internet_gateway.main.id}"
}

resource "aws_route" "public_default_v6" {
  route_table_id         = "${aws_route_table.main.id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = "${aws_internet_gateway.main.id}"
}

resource "aws_route_table_association" "public_us-east-1a" {
  subnet_id      = "${aws_subnet.public_us-east-1a.id}"
  route_table_id = "${aws_route_table.main.id}"
}

resource "aws_route_table_association" "public_us-east-1b" {
  subnet_id      = "${aws_subnet.public_us-east-1b.id}"
  route_table_id = "${aws_route_table.main.id}"
}

resource "aws_route_table_association" "public_us-east-1e" {
  subnet_id      = "${aws_subnet.public_us-east-1e.id}"
  route_table_id = "${aws_route_table.main.id}"
}

data "aws_iam_policy_document" "instance-assume-role-policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "dcgan-hubble" {
  name               = "dcgan-hubble"
  assume_role_policy = "${data.aws_iam_policy_document.instance-assume-role-policy.json}"
}

data "aws_iam_policy_document" "dcgan-hubble" {
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["${aws_s3_bucket.outputs.arn}"]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject",
    ]

    resources = ["${aws_s3_bucket.outputs.arn}/*"]
  }

  statement {
    effect = "Allow"

    actions   = ["s3:*"]
    resources = ["arn:aws:s3:::stpubdata", "arn:aws:s3:::stpubdata/*"]
  }
}

resource "aws_iam_policy" "dcgan-hubble" {
  name   = "dcgan-hubble"
  path   = "/"
  policy = "${data.aws_iam_policy_document.dcgan-hubble.json}"
}

resource "aws_iam_role_policy_attachment" "dcgan-hubble" {
  role       = "${aws_iam_role.dcgan-hubble.name}"
  policy_arn = "${aws_iam_policy.dcgan-hubble.arn}"
}

resource "aws_iam_instance_profile" "dcgan-hubble" {
  name = "dcgan-hubble"
  role = "dcgan-hubble"
}

resource "aws_key_pair" "shared" {
  key_name   = "shared"
  public_key = "${file("shared_ssh.key.pub")}"
}

resource "aws_spot_instance_request" "production" {
  spot_price                      = "1.000"
  instance_type                   = "p3.2xlarge"
  ami                             = "ami-09994a343440ce0cd"
  instance_interruption_behaviour = "stop"
  valid_until                     = "2018-09-16T00:00:00Z"
  spot_type                       = "persistent"
  associate_public_ip_address     = true
  subnet_id                       = "${aws_subnet.public_us-east-1a.id}"
  iam_instance_profile            = "dcgan-hubble"
  vpc_security_group_ids          = ["${aws_security_group.main.id}"]
  key_name                        = "${aws_key_pair.shared.key_name}"
  wait_for_fulfillment            = false

  tags = {
    Name = "production"
  }

  lifecycle {
    ignore_changes = ["ipv6_address_count", "ipv6_addresses", "root_block_device"]
  }
}

resource "aws_instance" "integration" {
  instance_type               = "t3.medium"
  ami                         = "ami-09994a343440ce0cd"
  associate_public_ip_address = true
  subnet_id                   = "${aws_subnet.public_us-east-1a.id}"
  iam_instance_profile        = "dcgan-hubble"
  vpc_security_group_ids      = ["${aws_security_group.main.id}"]
  key_name                    = "${aws_key_pair.shared.key_name}"

  credit_specification {
    cpu_credits = "unlimited"
  }

  tags = {
    Name = "integration"
  }
}

output "integration_ipv4" {
  value = "${aws_instance.integration.public_ip}"
}

output "integration_ipv6" {
  value = "${aws_instance.integration.ipv6_addresses}"
}

# data "aws_instance" "production" {
#   instance_tags {
#     Name = "production"
#   }
# }
# 
# output "production_ipv4" {
#   value = "${data.aws_instance.production.public_ip}"
# }
# 
# output "production_ipv6" {
#   value = "${data.aws_instance.production.ipv6_addresses}"
# }

